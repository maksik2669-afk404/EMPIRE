package mctun

import (
	"crypto/md5"
	"encoding/binary"
	"fmt"

	"app.empire/mc-tunnel/internal/mcproto"
)

// Protocol constants for Minecraft Java 1.20.1 (protocol 763). Packet IDs on
// the raw-protocol client side are version-specific; change this block to match
// the server you run. The server PLUGIN side needs none of these — Bukkit
// delivers plugin-channel bytes regardless of protocol version.
const (
	ProtocolVersion = 763

	// Handshake / Login (serverbound)
	pkHandshake  = 0x00
	pkLoginStart = 0x00

	// Login (clientbound)
	pkDisconnectLogin   = 0x00
	pkEncryptionRequest = 0x01
	pkLoginSuccess      = 0x02
	pkSetCompression    = 0x03

	// Play IDs (defaults for 1.20.1)
	PlayCustomPayloadClientbound = 0x18
	PlayCustomPayloadServerbound = 0x14
	PlayKeepAliveClientbound     = 0x23
	PlayKeepAliveServerbound     = 0x12
)

// offlineUUID derives the same UUID an offline-mode server assigns: MD5 of
// "OfflinePlayer:<name>" with the version/variant bits of a type-3 UUID.
func offlineUUID(name string) [16]byte {
	sum := md5.Sum([]byte("OfflinePlayer:" + name))
	sum[6] = (sum[6] & 0x0f) | 0x30
	sum[8] = (sum[8] & 0x3f) | 0x80
	return sum
}

// Login performs the handshake and an offline-mode login, leaving conn in the
// Play state. It returns an error for online-mode servers (which require Mojang
// authentication — a later milestone).
func Login(conn *mcproto.Conn, host string, port uint16, username string) error {
	hs := mcproto.AppendVarInt(nil, ProtocolVersion)
	hs = mcproto.AppendString(hs, host)
	var pb [2]byte
	binary.BigEndian.PutUint16(pb[:], port)
	hs = append(hs, pb[:]...)
	hs = mcproto.AppendVarInt(hs, 2) // next state: login
	if err := conn.WritePacket(pkHandshake, hs); err != nil {
		return err
	}

	ls := mcproto.AppendString(nil, username)
	uuid := offlineUUID(username)
	ls = append(ls, uuid[:]...)
	if err := conn.WritePacket(pkLoginStart, ls); err != nil {
		return err
	}

	for {
		id, data, err := conn.ReadPacket()
		if err != nil {
			return err
		}
		switch id {
		case pkSetCompression:
			threshold, _, err := mcproto.ReadVarInt(bytesReader(data))
			if err != nil {
				return err
			}
			conn.SetCompressionThreshold(int(threshold))
		case pkLoginSuccess:
			return nil // now in Play state
		case pkEncryptionRequest:
			return fmt.Errorf("mctun: server is in online mode; Mojang auth not yet supported")
		case pkDisconnectLogin:
			return fmt.Errorf("mctun: server refused login: %s", string(data))
		default:
			return fmt.Errorf("mctun: unexpected login packet id 0x%02x", id)
		}
	}
}

func bytesReader(b []byte) *byteReader { return &byteReader{b} }
