package mctun

import (
	"encoding/binary"
	"errors"
	"io"
	"net"
	"strconv"
)

// The first bytes a client writes on a freshly opened mux stream tell the
// server plugin where to connect. The encoding mirrors SOCKS5 address types so
// the client can forward a SOCKS request without reshaping it.
//
//	[ver=1][atyp][addr...][port:2]
//	atyp 1 = IPv4 (4 bytes), 3 = domain (1-byte length + bytes), 4 = IPv6 (16 bytes)
const dialVersion = 1

const (
	atypIPv4   = 1
	atypDomain = 3
	atypIPv6   = 4
)

// ErrBadDialHeader indicates a malformed connect header.
var ErrBadDialHeader = errors.New("mctun: bad dial header")

// EncodeDial builds the connect header for host:port.
func EncodeDial(host string, port uint16) []byte {
	out := []byte{dialVersion}
	if ip := net.ParseIP(host); ip != nil {
		if v4 := ip.To4(); v4 != nil {
			out = append(out, atypIPv4)
			out = append(out, v4...)
		} else {
			out = append(out, atypIPv6)
			out = append(out, ip.To16()...)
		}
	} else {
		if len(host) > 255 {
			host = host[:255]
		}
		out = append(out, atypDomain, byte(len(host)))
		out = append(out, host...)
	}
	var p [2]byte
	binary.BigEndian.PutUint16(p[:], port)
	return append(out, p[:]...)
}

// ReadDial reads and parses a connect header from r, returning "host:port".
func ReadDial(r io.Reader) (string, error) {
	var head [2]byte
	if _, err := io.ReadFull(r, head[:]); err != nil {
		return "", err
	}
	if head[0] != dialVersion {
		return "", ErrBadDialHeader
	}
	var host string
	switch head[1] {
	case atypIPv4:
		var b [4]byte
		if _, err := io.ReadFull(r, b[:]); err != nil {
			return "", err
		}
		host = net.IP(b[:]).String()
	case atypIPv6:
		var b [16]byte
		if _, err := io.ReadFull(r, b[:]); err != nil {
			return "", err
		}
		host = net.IP(b[:]).String()
	case atypDomain:
		var l [1]byte
		if _, err := io.ReadFull(r, l[:]); err != nil {
			return "", err
		}
		b := make([]byte, l[0])
		if _, err := io.ReadFull(r, b); err != nil {
			return "", err
		}
		host = string(b)
	default:
		return "", ErrBadDialHeader
	}
	var p [2]byte
	if _, err := io.ReadFull(r, p[:]); err != nil {
		return "", err
	}
	return net.JoinHostPort(host, strconv.Itoa(int(binary.BigEndian.Uint16(p[:])))), nil
}
