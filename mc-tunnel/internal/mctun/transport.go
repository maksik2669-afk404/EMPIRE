// Package mctun adapts the Minecraft custom-payload channel into the plain
// io.ReadWriteCloser that the mux expects. Outbound mux bytes are sized by the
// shaper and wrapped in Plugin Message packets on a private channel; inbound
// packets on that channel are reassembled into the byte stream. Packets on any
// other channel (and keepalives) are handled or ignored, so to a passive
// observer the connection carries ordinary modded-client plugin messages.
//
// Packet IDs differ between protocol versions, so they are configuration, not
// constants. The client and the server plugin must agree on the channel name;
// an unknown channel is silently ignored, which is also what makes an
// unauthenticated probe see nothing but a normal Minecraft session.
package mctun

import (
	"errors"
	"io"
	"math/rand"
	"sync"

	"app.empire/mc-tunnel/internal/mcproto"
	"app.empire/mc-tunnel/internal/shape"
)

// Config describes the version-specific packet IDs and the shaping parameters.
type Config struct {
	Channel          string         // private plugin channel, e.g. "mctunnel:d"
	CustomPayloadOut int32          // Plugin Message packet ID we send
	CustomPayloadIn  int32          // Plugin Message packet ID we receive
	KeepAliveIn      int32          // inbound KeepAlive ID, or -1 to disable
	KeepAliveOut     int32          // outbound KeepAlive ID
	Limiter          *shape.Limiter // throughput ceiling; nil disables pacing
	MinChunk         int            // min bytes per payload packet
	MaxChunk         int            // max bytes per payload packet
	Rand             *rand.Rand     // size randomness source
}

func (c Config) withDefaults() Config {
	if c.MinChunk <= 0 {
		c.MinChunk = 48
	}
	if c.MaxChunk < c.MinChunk {
		c.MaxChunk = 1024
	}
	if c.Rand == nil {
		c.Rand = rand.New(rand.NewSource(rand.Int63()))
	}
	if c.KeepAliveIn == 0 {
		c.KeepAliveIn = -1
	}
	return c
}

// Transport presents the private channel as an io.ReadWriteCloser.
type Transport struct {
	conn *mcproto.Conn
	cfg  Config

	mu   sync.Mutex
	cond *sync.Cond
	buf  []byte
	err  error

	closeOnce sync.Once
	wmu       sync.Mutex // serializes shaped writes (size/pace decisions)
}

// NewTransport starts the dispatch loop and returns the adapter.
func NewTransport(conn *mcproto.Conn, cfg Config) *Transport {
	t := &Transport{conn: conn, cfg: cfg.withDefaults()}
	t.cond = sync.NewCond(&t.mu)
	go t.readLoop()
	return t
}

func (t *Transport) readLoop() {
	for {
		id, data, err := t.conn.ReadPacket()
		if err != nil {
			t.fail(err)
			return
		}
		switch id {
		case t.cfg.CustomPayloadIn:
			payload, ok := stripChannel(data, t.cfg.Channel)
			if !ok {
				continue // some other plugin's message — not ours
			}
			t.mu.Lock()
			t.buf = append(t.buf, payload...)
			t.cond.Signal()
			t.mu.Unlock()
		case t.cfg.KeepAliveIn:
			if t.cfg.KeepAliveIn >= 0 {
				// Echo the KeepAlive so the server keeps us in the player list.
				_ = t.conn.WritePacket(t.cfg.KeepAliveOut, data)
			}
		default:
			// Ignore everything else (chunk data, entity updates, chat, ...).
		}
	}
}

func (t *Transport) fail(err error) {
	t.mu.Lock()
	if t.err == nil {
		t.err = err
	}
	t.cond.Broadcast()
	t.mu.Unlock()
}

// Read drains reassembled channel bytes.
func (t *Transport) Read(p []byte) (int, error) {
	t.mu.Lock()
	for len(t.buf) == 0 && t.err == nil {
		t.cond.Wait()
	}
	if len(t.buf) == 0 {
		err := t.err
		t.mu.Unlock()
		return 0, err
	}
	n := copy(p, t.buf)
	t.buf = t.buf[n:]
	t.mu.Unlock()
	return n, nil
}

// Write shapes p into payload packets on the private channel.
func (t *Transport) Write(p []byte) (int, error) {
	t.wmu.Lock()
	defer t.wmu.Unlock()

	total := 0
	for _, chunk := range shape.Split(p, t.cfg.MinChunk, t.cfg.MaxChunk, t.cfg.Rand) {
		if t.cfg.Limiter != nil {
			t.cfg.Limiter.Wait(len(chunk) + len(t.cfg.Channel) + 3)
		}
		body := mcproto.AppendString(nil, t.cfg.Channel)
		body = append(body, chunk...)
		if err := t.conn.WritePacket(t.cfg.CustomPayloadOut, body); err != nil {
			return total, err
		}
		total += len(chunk)
	}
	return total, nil
}

// Close marks the transport failed; the caller is expected to also close the
// underlying Minecraft connection (ending the "player" session).
func (t *Transport) Close() error {
	t.closeOnce.Do(func() { t.fail(errClosed) })
	return nil
}

var errClosed = errors.New("mctun: transport closed")

// stripChannel parses a Plugin Message body (channel string + payload) and
// returns the payload if the channel matches want.
func stripChannel(data []byte, want string) ([]byte, bool) {
	r := byteReader{data}
	n, _, err := mcproto.ReadVarInt(&r)
	if err != nil || n < 0 || int(n) > len(r.b) {
		return nil, false
	}
	ch := string(r.b[:n])
	if ch != want {
		return nil, false
	}
	return r.b[n:], true
}

// byteReader is a tiny io.Reader over a slice (ReadVarInt needs a reader).
type byteReader struct{ b []byte }

func (r *byteReader) Read(p []byte) (int, error) {
	if len(r.b) == 0 {
		return 0, io.EOF
	}
	n := copy(p, r.b)
	r.b = r.b[n:]
	return n, nil
}
