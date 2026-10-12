// Command mctun-client runs on the censored user's machine. It exposes a local
// SOCKS5 proxy, logs in to the cover Minecraft server as an ordinary player,
// and carries every proxied connection through the server's plugin channel.
//
// Point your browser/system SOCKS5 proxy at the --listen address.
//
// The Minecraft play-state packet IDs are pinned to 1.20.1 (see internal/mctun
// login.go); run a 1.20.1 server or adjust them. This binary is the live edge
// of the project — the audited, test-covered guarantees live in the library
// packages, not here.
package main

import (
	"flag"
	"io"
	"log"
	"math/rand"
	"net"
	"strconv"
	"time"

	"app.empire/mc-tunnel/internal/mcproto"
	"app.empire/mc-tunnel/internal/mctun"
	"app.empire/mc-tunnel/internal/mux"
	"app.empire/mc-tunnel/internal/shape"
)

func main() {
	listen := flag.String("listen", "127.0.0.1:1080", "local SOCKS5 listen address")
	server := flag.String("server", "", "cover Minecraft server host:port (required)")
	user := flag.String("user", "Steve", "player name to log in with")
	channel := flag.String("channel", "mctunnel:d", "private plugin channel (must match server)")
	rateKB := flag.Int("rate-kb", 2048, "throughput ceiling in KiB/s (0 = unlimited)")
	minChunk := flag.Int("min-chunk", 48, "minimum payload bytes per Minecraft packet")
	maxChunk := flag.Int("max-chunk", 1024, "maximum payload bytes per Minecraft packet")
	flag.Parse()

	if *server == "" {
		log.Fatal("--server is required, e.g. --server play.example.net:25565")
	}
	host, portStr, err := net.SplitHostPort(*server)
	if err != nil {
		log.Fatalf("bad --server: %v", err)
	}
	port64, err := strconv.ParseUint(portStr, 10, 16)
	if err != nil {
		log.Fatalf("bad server port: %v", err)
	}

	log.Printf("mctun-client build v4 | play IDs: custom_payload in=0x%02x out=0x%02x, keep_alive in=0x%02x out=0x%02x",
		mctun.PlayCustomPayloadClientbound, mctun.PlayCustomPayloadServerbound,
		mctun.PlayKeepAliveClientbound, mctun.PlayKeepAliveServerbound)

	session, err := dialServer(host, uint16(port64), *user, *channel, *rateKB, *minChunk, *maxChunk)
	if err != nil {
		log.Fatalf("connect to cover server: %v", err)
	}
	log.Printf("joined %s as %q; SOCKS5 on %s", *server, *user, *listen)

	ln, err := net.Listen("tcp", *listen)
	if err != nil {
		log.Fatalf("listen: %v", err)
	}
	for {
		c, err := ln.Accept()
		if err != nil {
			log.Printf("accept: %v", err)
			continue
		}
		go handleSOCKS(c, session)
	}
}

func dialServer(host string, port uint16, user, channel string, rateKB, minChunk, maxChunk int) (*mux.Session, error) {
	raw, err := net.DialTimeout("tcp", net.JoinHostPort(host, strconv.Itoa(int(port))), 15*time.Second)
	if err != nil {
		return nil, err
	}
	conn := mcproto.NewConn(raw)
	if err := mctun.Login(conn, host, port, user); err != nil {
		raw.Close()
		return nil, err
	}
	// Announce the channel the way a modded client would.
	reg := mcproto.AppendString(nil, "minecraft:register")
	reg = append(reg, []byte(channel+"\x00")...)
	_ = conn.WritePacket(mctun.PlayCustomPayloadServerbound, reg)

	var limiter *shape.Limiter
	if rateKB > 0 {
		limiter = shape.NewLimiter(rateKB*1024, rateKB*1024)
	}
	tr := mctun.NewTransport(conn, mctun.Config{
		Channel:          channel,
		CustomPayloadOut: mctun.PlayCustomPayloadServerbound,
		CustomPayloadIn:  mctun.PlayCustomPayloadClientbound,
		KeepAliveIn:      mctun.PlayKeepAliveClientbound,
		KeepAliveOut:     mctun.PlayKeepAliveServerbound,
		Limiter:          limiter,
		MinChunk:         minChunk,
		MaxChunk:         maxChunk,
		Rand:             rand.New(rand.NewSource(time.Now().UnixNano())),
	})
	return mux.Client(tr), nil
}

// handleSOCKS implements the minimal SOCKS5 CONNECT handshake and bridges the
// client connection to a new tunnel stream.
func handleSOCKS(c net.Conn, session *mux.Session) {
	defer c.Close()
	host, port, err := socksHandshake(c)
	if err != nil {
		return
	}
	st, err := session.Open()
	if err != nil {
		log.Printf("open stream: %v", err)
		return
	}
	defer st.Close()
	if _, err := st.Write(mctun.EncodeDial(host, port)); err != nil {
		return
	}
	done := make(chan struct{}, 2)
	go func() { io.Copy(st, c); done <- struct{}{} }()
	go func() { io.Copy(c, st); done <- struct{}{} }()
	<-done
}

// socksHandshake performs the SOCKS5 greeting and CONNECT request, replies
// success, and returns the requested destination.
func socksHandshake(c net.Conn) (string, uint16, error) {
	buf := make([]byte, 262)
	// Greeting: VER, NMETHODS, METHODS...
	if _, err := io.ReadFull(c, buf[:2]); err != nil {
		return "", 0, err
	}
	if buf[0] != 0x05 {
		return "", 0, errProto
	}
	if _, err := io.ReadFull(c, buf[:buf[1]]); err != nil {
		return "", 0, err
	}
	if _, err := c.Write([]byte{0x05, 0x00}); err != nil { // no auth
		return "", 0, err
	}
	// Request: VER, CMD, RSV, ATYP
	if _, err := io.ReadFull(c, buf[:4]); err != nil {
		return "", 0, err
	}
	if buf[1] != 0x01 { // only CONNECT
		c.Write([]byte{0x05, 0x07, 0x00, 0x01, 0, 0, 0, 0, 0, 0})
		return "", 0, errProto
	}
	var host string
	switch buf[3] {
	case 0x01:
		if _, err := io.ReadFull(c, buf[:4]); err != nil {
			return "", 0, err
		}
		host = net.IP(buf[:4]).String()
	case 0x03:
		if _, err := io.ReadFull(c, buf[:1]); err != nil {
			return "", 0, err
		}
		n := int(buf[0])
		if _, err := io.ReadFull(c, buf[:n]); err != nil {
			return "", 0, err
		}
		host = string(buf[:n])
	case 0x04:
		if _, err := io.ReadFull(c, buf[:16]); err != nil {
			return "", 0, err
		}
		host = net.IP(buf[:16]).String()
	default:
		return "", 0, errProto
	}
	if _, err := io.ReadFull(c, buf[:2]); err != nil {
		return "", 0, err
	}
	port := uint16(buf[0])<<8 | uint16(buf[1])
	// Reply success with a zero bind address.
	if _, err := c.Write([]byte{0x05, 0x00, 0x00, 0x01, 0, 0, 0, 0, 0, 0}); err != nil {
		return "", 0, err
	}
	return host, port, nil
}

type protoErr struct{}

func (protoErr) Error() string { return "socks: protocol error" }

var errProto = protoErr{}
