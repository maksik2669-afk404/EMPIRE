package mctun

import (
	"crypto/md5"
	"encoding/binary"
	"encoding/hex"
	"fmt"

	"app.empire/mc-tunnel/internal/mcauth"
	"app.empire/mc-tunnel/internal/mcproto"
)

// Protocol constants for Minecraft Java 1.20.1 (protocol 763). Packet IDs on
// the raw-protocol client side are version-specific; change this block to match
// the server you run. The server PLUGIN side needs none of these — Bukkit
// delivers plugin-channel bytes regardless of protocol version.
const (
	ProtocolVersion = 763

	// Handshake / Login (serverbound)
	pkHandshake          = 0x00
	pkLoginStart         = 0x00
	pkEncryptionResponse = 0x01

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

// Session is an authenticated Minecraft account used for online-mode login.
// Obtain it from package auth (Microsoft device-code flow) or supply a token
// captured elsewhere.
type Session struct {
	AccessToken string
	Name        string
	UUID        [16]byte
}

// JoinFunc proves to Mojang's session server that this client is joining the
// cover server. It must POST {accessToken, selectedProfile, serverId} to
// sessionserver.mojang.com/session/minecraft/join and return nil on HTTP 204.
// It is injected so the handshake can be tested without Mojang.
type JoinFunc func(accessToken, profileUUIDHex, serverHash string) error

// offlineUUID derives the same UUID an offline-mode server assigns: MD5 of
// "OfflinePlayer:<name>" with the version/variant bits of a type-3 UUID.
func offlineUUID(name string) [16]byte {
	sum := md5.Sum([]byte("OfflinePlayer:" + name))
	sum[6] = (sum[6] & 0x0f) | 0x30
	sum[8] = (sum[8] & 0x3f) | 0x80
	return sum
}

func writeHandshake(conn *mcproto.Conn, host string, port uint16) error {
	hs := mcproto.AppendVarInt(nil, ProtocolVersion)
	hs = mcproto.AppendString(hs, host)
	var pb [2]byte
	binary.BigEndian.PutUint16(pb[:], port)
	hs = append(hs, pb[:]...)
	hs = mcproto.AppendVarInt(hs, 2) // next state: login
	return conn.WritePacket(pkHandshake, hs)
}

func writeLoginStart(conn *mcproto.Conn, name string, uuid [16]byte) error {
	ls := mcproto.AppendString(nil, name)
	ls = append(ls, uuid[:]...)
	return conn.WritePacket(pkLoginStart, ls)
}

// Login performs an offline-mode login, leaving conn in the Play state. It
// errors on online-mode servers (which send an Encryption Request).
func Login(conn *mcproto.Conn, host string, port uint16, username string) error {
	if err := writeHandshake(conn, host, port); err != nil {
		return err
	}
	if err := writeLoginStart(conn, username, offlineUUID(username)); err != nil {
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
			return nil
		case pkEncryptionRequest:
			return fmt.Errorf("mctun: server is in online mode; use LoginOnline")
		case pkDisconnectLogin:
			return fmt.Errorf("mctun: server refused login: %s", string(data))
		default:
			return fmt.Errorf("mctun: unexpected login packet id 0x%02x", id)
		}
	}
}

// LoginOnline performs an online-mode login: it answers the server's Encryption
// Request with an RSA-sealed shared secret, proves the join to Mojang via join,
// switches the stream to AES/CFB8, and leaves conn in the Play state.
func LoginOnline(conn *mcproto.Conn, host string, port uint16, s Session, join JoinFunc) error {
	if err := writeHandshake(conn, host, port); err != nil {
		return err
	}
	if err := writeLoginStart(conn, s.Name, s.UUID); err != nil {
		return err
	}
	for {
		id, data, err := conn.ReadPacket()
		if err != nil {
			return err
		}
		switch id {
		case pkEncryptionRequest:
			if err := answerEncryption(conn, data, s, join); err != nil {
				return err
			}
			// Subsequent packets arrive encrypted; keep reading.
		case pkSetCompression:
			threshold, _, err := mcproto.ReadVarInt(bytesReader(data))
			if err != nil {
				return err
			}
			conn.SetCompressionThreshold(int(threshold))
		case pkLoginSuccess:
			return nil
		case pkDisconnectLogin:
			return fmt.Errorf("mctun: server refused login: %s", string(data))
		default:
			return fmt.Errorf("mctun: unexpected login packet id 0x%02x", id)
		}
	}
}

func answerEncryption(conn *mcproto.Conn, data []byte, s Session, join JoinFunc) error {
	r := bytesReader(data)
	serverID, err := readString(r)
	if err != nil {
		return err
	}
	pubKeyDER, err := readBytes(r)
	if err != nil {
		return err
	}
	verifyToken, err := readBytes(r)
	if err != nil {
		return err
	}

	pub, err := mcauth.ParsePublicKey(pubKeyDER)
	if err != nil {
		return err
	}
	secret, err := mcauth.NewSharedSecret()
	if err != nil {
		return err
	}

	hash := mcauth.AuthDigest(serverID, secret, pubKeyDER)
	if join != nil {
		if err := join(s.AccessToken, hex.EncodeToString(s.UUID[:]), hash); err != nil {
			return fmt.Errorf("mctun: session join failed: %w", err)
		}
	}

	encSecret, err := mcauth.Encrypt(pub, secret)
	if err != nil {
		return err
	}
	encToken, err := mcauth.Encrypt(pub, verifyToken)
	if err != nil {
		return err
	}
	body := mcproto.AppendVarInt(nil, int32(len(encSecret)))
	body = append(body, encSecret...)
	body = mcproto.AppendVarInt(body, int32(len(encToken)))
	body = append(body, encToken...)
	if err := conn.WritePacket(pkEncryptionResponse, body); err != nil {
		return err
	}
	// From here the whole stream is AES/CFB8 with the shared secret.
	return conn.EnableEncryption(secret)
}

func readString(r *byteReader) (string, error) {
	b, err := readBytes(r)
	return string(b), err
}

func readBytes(r *byteReader) ([]byte, error) {
	n, _, err := mcproto.ReadVarInt(r)
	if err != nil {
		return nil, err
	}
	if n < 0 || int(n) > len(r.b) {
		return nil, fmt.Errorf("mctun: length %d out of range", n)
	}
	out := make([]byte, n)
	if _, err := r.Read(out); err != nil {
		return nil, err
	}
	return out, nil
}

func bytesReader(b []byte) *byteReader { return &byteReader{b} }
