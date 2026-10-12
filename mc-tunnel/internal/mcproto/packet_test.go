package mcproto

import (
	"bytes"
	"crypto/rand"
	"io"
	"net"
	"testing"
)

type rw struct {
	io.Reader
	io.Writer
}

func pair(t *testing.T) (*Conn, *Conn, func()) {
	t.Helper()
	a, b := net.Pipe()
	return NewConn(a), NewConn(b), func() { a.Close(); b.Close() }
}

func roundTrip(t *testing.T, ca, cb *Conn, id int32, data []byte) {
	t.Helper()
	errc := make(chan error, 1)
	go func() { errc <- ca.WritePacket(id, data) }()
	gotID, got, err := cb.ReadPacket()
	if err != nil {
		t.Fatalf("ReadPacket: %v", err)
	}
	if werr := <-errc; werr != nil {
		t.Fatalf("WritePacket: %v", werr)
	}
	if gotID != id || !bytes.Equal(got, data) {
		t.Fatalf("round trip id=%d len=%d -> id=%d len=%d", id, len(data), gotID, len(got))
	}
}

func TestPacketUncompressed(t *testing.T) {
	ca, cb, done := pair(t)
	defer done()
	roundTrip(t, ca, cb, 0x00, []byte("handshake payload"))
	roundTrip(t, ca, cb, 0x7f, nil)
}

func TestPacketCompressionBelowThreshold(t *testing.T) {
	ca, cb, done := pair(t)
	defer done()
	ca.SetCompressionThreshold(256)
	cb.SetCompressionThreshold(256)
	roundTrip(t, ca, cb, 0x10, []byte("short, stored uncompressed"))
}

func TestPacketCompressionAboveThreshold(t *testing.T) {
	ca, cb, done := pair(t)
	defer done()
	ca.SetCompressionThreshold(64)
	cb.SetCompressionThreshold(64)
	big := bytes.Repeat([]byte("minecraft-custom-payload-"), 1000)
	roundTrip(t, ca, cb, 0x18, big)
}

func TestPacketEncrypted(t *testing.T) {
	ca, cb, done := pair(t)
	defer done()
	secret := make([]byte, 16)
	if _, err := rand.Read(secret); err != nil {
		t.Fatal(err)
	}
	if err := ca.EnableEncryption(secret); err != nil {
		t.Fatal(err)
	}
	if err := cb.EnableEncryption(secret); err != nil {
		t.Fatal(err)
	}
	ca.SetCompressionThreshold(32)
	cb.SetCompressionThreshold(32)
	for i := 0; i < 5; i++ {
		roundTrip(t, ca, cb, int32(i), bytes.Repeat([]byte{byte(i)}, i*50))
	}
}

func TestReadPacketTooBig(t *testing.T) {
	var buf bytes.Buffer
	buf.Write(AppendVarInt(nil, MaxPacketSize+1))
	c := NewConn(&rw{Reader: &buf, Writer: &bytes.Buffer{}})
	if _, _, err := c.ReadPacket(); err != ErrPacketTooBig {
		t.Fatalf("got %v, want ErrPacketTooBig", err)
	}
}
