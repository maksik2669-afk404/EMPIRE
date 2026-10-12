package mctun

import (
	"bytes"
	"crypto/rand"
	"io"
	"net"
	"sync"
	"testing"
	"time"

	"app.empire/mc-tunnel/internal/mcproto"
	"app.empire/mc-tunnel/internal/mux"
)

// Two transports back-to-back over an in-memory pipe stand in for client and
// server plugin: it exercises the whole data path (mux -> custom payload ->
// mux) without any Minecraft server or authentication.
func testConfig() Config {
	return Config{
		Channel:          "mctunnel:d",
		CustomPayloadOut: 0x12,
		CustomPayloadIn:  0x12,
		KeepAliveIn:      -1,
		MinChunk:         48,
		MaxChunk:         512,
	}
}

func TestTransportMuxEndToEnd(t *testing.T) {
	a, b := net.Pipe()
	ta := NewTransport(mcproto.NewConn(a), testConfig())
	tb := NewTransport(mcproto.NewConn(b), testConfig())
	defer func() { ta.Close(); tb.Close(); a.Close(); b.Close() }()

	client := mux.Client(ta)
	server := mux.Server(tb)
	defer client.Close()
	defer server.Close()

	// Server echoes each stream.
	go func() {
		for {
			st, err := server.Accept()
			if err != nil {
				return
			}
			go func(st *mux.Stream) { io.Copy(st, st); st.Close() }(st)
		}
	}()

	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			st, err := client.Open()
			if err != nil {
				t.Errorf("open: %v", err)
				return
			}
			msg := make([]byte, 5000+i*111)
			rand.Read(msg)
			go st.Write(msg)
			got := make([]byte, len(msg))
			if _, err := io.ReadFull(st, got); err != nil {
				t.Errorf("read: %v", err)
				return
			}
			if !bytes.Equal(got, msg) {
				t.Errorf("stream %d mismatch", i)
			}
			st.Close()
		}(i)
	}
	done := make(chan struct{})
	go func() { wg.Wait(); close(done) }()
	select {
	case <-done:
	case <-time.After(15 * time.Second):
		t.Fatal("timeout")
	}
}

func TestStripChannelRejectsOther(t *testing.T) {
	body := mcproto.AppendString(nil, "minecraft:brand")
	body = append(body, []byte("vanilla")...)
	if _, ok := stripChannel(body, "mctunnel:d"); ok {
		t.Fatal("accepted a foreign channel")
	}
	ours := mcproto.AppendString(nil, "mctunnel:d")
	ours = append(ours, []byte("payload")...)
	got, ok := stripChannel(ours, "mctunnel:d")
	if !ok || string(got) != "payload" {
		t.Fatalf("own channel: ok=%v got=%q", ok, got)
	}
}
