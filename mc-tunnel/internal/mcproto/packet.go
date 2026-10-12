package mcproto

import (
	"bytes"
	"compress/zlib"
	"crypto/aes"
	"crypto/cipher"
	"errors"
	"fmt"
	"io"
	"sync"
)

// MaxPacketSize bounds an inbound packet body so a hostile or corrupt peer
// cannot make us allocate without limit. 2 MiB is well above any real
// Minecraft packet (chunk data aside, which we never request as a fake client).
const MaxPacketSize = 2 << 20

// ErrPacketTooBig is returned when an inbound packet exceeds MaxPacketSize.
var ErrPacketTooBig = errors.New("mcproto: packet exceeds maximum size")

// Conn frames Minecraft packets over an ordered byte stream (a TCP connection).
//
// Reads and writes happen byte-exact: no buffering reads ahead of a packet
// boundary, so EnableEncryption can swap the underlying stream cipher in at
// the exact handshake boundary (online mode) without losing bytes.
type Conn struct {
	r         io.Reader
	w         io.Writer
	threshold int // compression threshold; <0 means compression disabled
	wmu       sync.Mutex
}

// NewConn wraps an ordered, reliable byte stream (typically a *net.TCPConn).
func NewConn(rw io.ReadWriter) *Conn {
	return &Conn{r: rw, w: rw, threshold: -1}
}

// SetCompressionThreshold enables compression for packets whose uncompressed
// body is at least threshold bytes. A negative threshold disables compression.
// It must be called to mirror the server's Set Compression packet.
func (c *Conn) SetCompressionThreshold(threshold int) { c.threshold = threshold }

// EnableEncryption switches the stream to AES-128/CFB8 with the given 16-byte
// shared secret used as both key and IV, as Minecraft does after login. It must
// be called exactly at the encryption boundary; no bytes are buffered across it.
func (c *Conn) EnableEncryption(sharedSecret []byte) error {
	block, err := aes.NewCipher(sharedSecret)
	if err != nil {
		return err
	}
	c.r = cipher.StreamReader{S: newCFB8(block, sharedSecret, true), R: c.r}
	c.w = cipher.StreamWriter{S: newCFB8(block, sharedSecret, false), W: c.w}
	return nil
}

// WritePacket writes a packet with the given ID and body, applying compression
// when enabled and the body is large enough.
func (c *Conn) WritePacket(id int32, data []byte) error {
	c.wmu.Lock()
	defer c.wmu.Unlock()

	raw := AppendVarInt(make([]byte, 0, VarIntLen(id)+len(data)), id)
	raw = append(raw, data...)

	var body []byte
	if c.threshold < 0 {
		body = raw
	} else if len(raw) < c.threshold {
		// Below threshold: data length prefix of 0 means "stored uncompressed".
		body = AppendVarInt(nil, 0)
		body = append(body, raw...)
	} else {
		var buf bytes.Buffer
		zw := zlib.NewWriter(&buf)
		if _, err := zw.Write(raw); err != nil {
			return err
		}
		if err := zw.Close(); err != nil {
			return err
		}
		body = AppendVarInt(nil, int32(len(raw)))
		body = append(body, buf.Bytes()...)
	}

	out := AppendVarInt(make([]byte, 0, VarIntLen(int32(len(body)))+len(body)), int32(len(body)))
	out = append(out, body...)
	_, err := c.w.Write(out)
	return err
}

// ReadPacket reads the next packet, returning its ID and body.
func (c *Conn) ReadPacket() (id int32, data []byte, err error) {
	length, _, err := ReadVarInt(c.r)
	if err != nil {
		return 0, nil, err
	}
	if length < 0 || int(length) > MaxPacketSize {
		return 0, nil, ErrPacketTooBig
	}
	buf := make([]byte, length)
	if _, err := io.ReadFull(c.r, buf); err != nil {
		return 0, nil, err
	}

	rest := buf
	if c.threshold >= 0 {
		dataLen, n, err := ReadVarInt(bytes.NewReader(buf))
		if err != nil {
			return 0, nil, err
		}
		rest = buf[n:]
		if dataLen != 0 {
			if int(dataLen) > MaxPacketSize {
				return 0, nil, ErrPacketTooBig
			}
			zr, err := zlib.NewReader(bytes.NewReader(rest))
			if err != nil {
				return 0, nil, err
			}
			decompressed, err := io.ReadAll(io.LimitReader(zr, int64(dataLen)+1))
			if cerr := zr.Close(); err == nil {
				err = cerr
			}
			if err != nil {
				return 0, nil, err
			}
			if len(decompressed) != int(dataLen) {
				return 0, nil, fmt.Errorf("mcproto: declared data length %d, got %d", dataLen, len(decompressed))
			}
			rest = decompressed
		}
	}

	pr := bytes.NewReader(rest)
	id, n, err := ReadVarInt(pr)
	if err != nil {
		return 0, nil, err
	}
	return id, rest[n:], nil
}
