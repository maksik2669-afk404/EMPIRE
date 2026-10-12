// Package mux is a small stream multiplexer that runs many independent,
// reliable byte streams over one ordered transport (here: the Minecraft
// custom-payload channel between client and server plugin).
//
// It is deliberately tiny and dependency-free so the whole data path can be
// audited. Each stream has a fixed receive window; the reader replenishes the
// sender's credit as it consumes bytes, which bounds memory and stops one busy
// stream from stalling the others (head-of-line blocking) on the shared link.
//
// Stream-ID parity keeps the two ends from colliding: the client opens odd IDs,
// the server opens even ones. Closing is full-duplex (a FIN tears the whole
// stream down); half-open streams are a later refinement.
package mux

import (
	"encoding/binary"
	"errors"
	"io"
	"sync"
	"time"
)

const (
	cmdSYN = 1 // open a new stream
	cmdPSH = 2 // stream data
	cmdFIN = 3 // close a stream
	cmdNOP = 4 // keepalive / cover traffic
	cmdWND = 5 // return receive-window credit (4-byte big-endian count)

	headerSize    = 7
	maxFrameData  = 65535
	initialWindow = 256 * 1024
)

// ErrSessionClosed is returned once the underlying transport is gone.
var ErrSessionClosed = errors.New("mux: session closed")

// ErrStreamClosed is returned when writing to a locally closed stream.
var ErrStreamClosed = errors.New("mux: stream closed")

// KeepaliveInterval is how often an idle session emits a NOP. Besides keeping
// the Minecraft connection alive, these frames are the natural hook for cover
// traffic so an idle tunnel still looks like a connected player.
var KeepaliveInterval = 15 * time.Second

type frame struct {
	cmd  uint8
	sid  uint32
	data []byte
}

func writeFrame(w io.Writer, f frame) error {
	var h [headerSize]byte
	h[0] = f.cmd
	binary.BigEndian.PutUint32(h[1:5], f.sid)
	binary.BigEndian.PutUint16(h[5:7], uint16(len(f.data)))
	if _, err := w.Write(h[:]); err != nil {
		return err
	}
	if len(f.data) > 0 {
		if _, err := w.Write(f.data); err != nil {
			return err
		}
	}
	return nil
}

func readFrame(r io.Reader) (frame, error) {
	var h [headerSize]byte
	if _, err := io.ReadFull(r, h[:]); err != nil {
		return frame{}, err
	}
	n := binary.BigEndian.Uint16(h[5:7])
	var data []byte
	if n > 0 {
		data = make([]byte, n)
		if _, err := io.ReadFull(r, data); err != nil {
			return frame{}, err
		}
	}
	return frame{cmd: h[0], sid: binary.BigEndian.Uint32(h[1:5]), data: data}, nil
}

// Session multiplexes streams over conn.
type Session struct {
	conn   io.ReadWriteCloser
	sendmu sync.Mutex // serializes transport writes

	mu      sync.Mutex
	streams map[uint32]*Stream
	nextID  uint32
	accept  chan *Stream

	die       chan struct{}
	closeOnce sync.Once
	err       error
}

// Client starts a session that opens odd-numbered streams.
func Client(conn io.ReadWriteCloser) *Session { return newSession(conn, 1) }

// Server starts a session that opens even-numbered streams.
func Server(conn io.ReadWriteCloser) *Session { return newSession(conn, 2) }

func newSession(conn io.ReadWriteCloser, firstID uint32) *Session {
	s := &Session{
		conn:    conn,
		streams: make(map[uint32]*Stream),
		nextID:  firstID,
		accept:  make(chan *Stream, 16),
		die:     make(chan struct{}),
	}
	go s.readLoop()
	go s.keepalive()
	return s
}

func (s *Session) writeFrame(f frame) error {
	s.sendmu.Lock()
	defer s.sendmu.Unlock()
	return writeFrame(s.conn, f)
}

// Open creates a new outbound stream.
func (s *Session) Open() (*Stream, error) {
	s.mu.Lock()
	select {
	case <-s.die:
		s.mu.Unlock()
		return nil, s.err
	default:
	}
	id := s.nextID
	s.nextID += 2
	st := newStream(id, s)
	s.streams[id] = st
	s.mu.Unlock()

	if err := s.writeFrame(frame{cmd: cmdSYN, sid: id}); err != nil {
		s.removeStream(id)
		return nil, err
	}
	return st, nil
}

// Accept returns the next inbound stream opened by the peer.
func (s *Session) Accept() (*Stream, error) {
	select {
	case st := <-s.accept:
		return st, nil
	case <-s.die:
		return nil, s.err
	}
}

// Close tears down the session and all its streams.
func (s *Session) Close() error { return s.closeWith(ErrSessionClosed) }

func (s *Session) closeWith(err error) error {
	s.closeOnce.Do(func() {
		s.err = err
		close(s.die)
		s.conn.Close()
		s.mu.Lock()
		for _, st := range s.streams {
			st.fail(err)
		}
		s.streams = map[uint32]*Stream{}
		s.mu.Unlock()
	})
	return nil
}

func (s *Session) removeStream(id uint32) {
	s.mu.Lock()
	delete(s.streams, id)
	s.mu.Unlock()
}

func (s *Session) stream(id uint32) *Stream {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.streams[id]
}

func (s *Session) readLoop() {
	for {
		f, err := readFrame(s.conn)
		if err != nil {
			s.closeWith(err)
			return
		}
		switch f.cmd {
		case cmdSYN:
			st := newStream(f.sid, s)
			s.mu.Lock()
			s.streams[f.sid] = st
			s.mu.Unlock()
			select {
			case s.accept <- st:
			case <-s.die:
				return
			}
		case cmdPSH:
			if st := s.stream(f.sid); st != nil {
				st.pushData(f.data)
			}
		case cmdWND:
			if len(f.data) == 4 {
				if st := s.stream(f.sid); st != nil {
					st.addSendWindow(int(binary.BigEndian.Uint32(f.data)))
				}
			}
		case cmdFIN:
			if st := s.stream(f.sid); st != nil {
				st.remoteClose()
				s.removeStream(f.sid)
			}
		case cmdNOP:
		}
	}
}

func (s *Session) keepalive() {
	t := time.NewTicker(KeepaliveInterval)
	defer t.Stop()
	for {
		select {
		case <-s.die:
			return
		case <-t.C:
			if err := s.writeFrame(frame{cmd: cmdNOP}); err != nil {
				return
			}
		}
	}
}

// Stream is one multiplexed, reliable byte stream. It satisfies io.ReadWriteCloser.
type Stream struct {
	id   uint32
	sess *Session

	mu         sync.Mutex
	readCond   *sync.Cond
	sendCond   *sync.Cond
	buf        []byte
	sendWindow int
	remoteEOF  bool
	localDone  bool
	err        error
}

func newStream(id uint32, s *Session) *Stream {
	st := &Stream{id: id, sess: s, sendWindow: initialWindow}
	st.readCond = sync.NewCond(&st.mu)
	st.sendCond = sync.NewCond(&st.mu)
	return st
}

func (st *Stream) pushData(data []byte) {
	st.mu.Lock()
	st.buf = append(st.buf, data...)
	st.readCond.Signal()
	st.mu.Unlock()
}

func (st *Stream) addSendWindow(n int) {
	st.mu.Lock()
	st.sendWindow += n
	st.sendCond.Broadcast()
	st.mu.Unlock()
}

func (st *Stream) remoteClose() {
	st.mu.Lock()
	st.remoteEOF = true
	st.readCond.Broadcast()
	st.mu.Unlock()
}

func (st *Stream) fail(err error) {
	st.mu.Lock()
	if st.err == nil {
		st.err = err
	}
	st.readCond.Broadcast()
	st.sendCond.Broadcast()
	st.mu.Unlock()
}

// Read implements io.Reader.
func (st *Stream) Read(p []byte) (int, error) {
	st.mu.Lock()
	for len(st.buf) == 0 && !st.remoteEOF && st.err == nil {
		st.readCond.Wait()
	}
	if len(st.buf) == 0 {
		err := st.err
		st.mu.Unlock()
		if err != nil {
			return 0, err
		}
		return 0, io.EOF
	}
	n := copy(p, st.buf)
	st.buf = st.buf[n:]
	st.mu.Unlock()

	// Give the credit back so the sender may transmit n more bytes.
	var c [4]byte
	binary.BigEndian.PutUint32(c[:], uint32(n))
	_ = st.sess.writeFrame(frame{cmd: cmdWND, sid: st.id, data: c[:]})
	return n, nil
}

// Write implements io.Writer, respecting the peer's receive window.
func (st *Stream) Write(p []byte) (int, error) {
	total := 0
	for len(p) > 0 {
		st.mu.Lock()
		for st.sendWindow == 0 && st.err == nil && !st.localDone {
			st.sendCond.Wait()
		}
		if st.err != nil {
			err := st.err
			st.mu.Unlock()
			return total, err
		}
		if st.localDone {
			st.mu.Unlock()
			return total, ErrStreamClosed
		}
		n := len(p)
		if n > st.sendWindow {
			n = st.sendWindow
		}
		if n > maxFrameData {
			n = maxFrameData
		}
		st.sendWindow -= n
		st.mu.Unlock()

		if err := st.sess.writeFrame(frame{cmd: cmdPSH, sid: st.id, data: p[:n]}); err != nil {
			return total, err
		}
		total += n
		p = p[n:]
	}
	return total, nil
}

// Close closes the stream and notifies the peer.
func (st *Stream) Close() error {
	st.mu.Lock()
	if st.localDone {
		st.mu.Unlock()
		return nil
	}
	st.localDone = true
	st.sendCond.Broadcast()
	st.mu.Unlock()

	err := st.sess.writeFrame(frame{cmd: cmdFIN, sid: st.id})
	st.sess.removeStream(st.id)
	return err
}

// ID returns the stream identifier (useful for logging).
func (st *Stream) ID() uint32 { return st.id }
