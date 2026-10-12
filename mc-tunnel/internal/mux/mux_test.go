package mux

import (
	"bytes"
	"crypto/rand"
	"io"
	"net"
	"sync"
	"testing"
	"time"
)

// echoServer accepts every inbound stream and echoes it back.
func echoServer(s *Session) {
	for {
		st, err := s.Accept()
		if err != nil {
			return
		}
		go func(st *Stream) {
			io.Copy(st, st)
			st.Close()
		}(st)
	}
}

func TestMuxEchoManyStreams(t *testing.T) {
	c, srv := net.Pipe()
	defer c.Close()
	defer srv.Close()
	client := Client(c)
	server := Server(srv)
	defer client.Close()
	defer server.Close()
	go echoServer(server)

	var wg sync.WaitGroup
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			st, err := client.Open()
			if err != nil {
				t.Errorf("open: %v", err)
				return
			}
			msg := bytes.Repeat([]byte{byte(i)}, 1000+i)
			if _, err := st.Write(msg); err != nil {
				t.Errorf("write: %v", err)
				return
			}
			got := make([]byte, len(msg))
			if _, err := io.ReadFull(st, got); err != nil {
				t.Errorf("read: %v", err)
				return
			}
			if !bytes.Equal(got, msg) {
				t.Errorf("stream %d: echo mismatch", i)
			}
			st.Close()
		}(i)
	}
	done := make(chan struct{})
	go func() { wg.Wait(); close(done) }()
	select {
	case <-done:
	case <-time.After(10 * time.Second):
		t.Fatal("timeout: possible deadlock")
	}
}

// TestMuxLargeTransfer pushes far more than one receive window through a single
// stream to exercise flow control and prove there is no head-of-line deadlock.
func TestMuxLargeTransfer(t *testing.T) {
	c, srv := net.Pipe()
	defer c.Close()
	defer srv.Close()
	client := Client(c)
	server := Server(srv)
	defer client.Close()
	defer server.Close()
	go echoServer(server)

	st, err := client.Open()
	if err != nil {
		t.Fatal(err)
	}
	payload := make([]byte, 4*initialWindow+12345)
	rand.Read(payload)

	got := make([]byte, len(payload))
	readDone := make(chan error, 1)
	go func() {
		_, err := io.ReadFull(st, got)
		readDone <- err
	}()

	if _, err := st.Write(payload); err != nil {
		t.Fatalf("write: %v", err)
	}
	select {
	case err := <-readDone:
		if err != nil {
			t.Fatalf("read: %v", err)
		}
	case <-time.After(15 * time.Second):
		t.Fatal("timeout: flow-control deadlock")
	}
	if !bytes.Equal(got, payload) {
		t.Fatal("large transfer corrupted")
	}
}

func TestMuxCloseUnblocksPeers(t *testing.T) {
	c, srv := net.Pipe()
	client := Client(c)
	server := Server(srv)
	go echoServer(server)

	st, err := client.Open()
	if err != nil {
		t.Fatal(err)
	}
	client.Close()
	srv.Close()

	if _, err := st.Read(make([]byte, 16)); err == nil {
		t.Fatal("expected error after session close")
	}
}
