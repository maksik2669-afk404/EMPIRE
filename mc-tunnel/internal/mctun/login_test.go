package mctun

import (
	"bytes"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"net"
	"testing"
	"time"

	"app.empire/mc-tunnel/internal/mcauth"
	"app.empire/mc-tunnel/internal/mcproto"
)

// A fake online-mode server verifies the whole encryption handshake end to end
// without Mojang: it issues an Encryption Request, decrypts the client's sealed
// secret, recomputes the server hash, switches to AES/CFB8, and only a correctly
// encrypted Login Success lets the client's LoginOnline return. The recomputed
// hash is compared against the one the client fed to its JoinFunc.
func TestLoginOnlineHandshake(t *testing.T) {
	cConn, sConn := net.Pipe()
	defer cConn.Close()
	defer sConn.Close()

	priv, err := rsa.GenerateKey(rand.Reader, 1024)
	if err != nil {
		t.Fatal(err)
	}
	der, err := x509.MarshalPKIXPublicKey(&priv.PublicKey)
	if err != nil {
		t.Fatal(err)
	}

	serverHashCh := make(chan string, 1)
	serverErr := make(chan error, 1)
	go func() {
		serverErr <- fakeOnlineServer(mcproto.NewConn(sConn), priv, der, serverHashCh)
	}()

	var joinUUID, joinHash, joinToken string
	session := Session{AccessToken: "tok", Name: "Tester", UUID: [16]byte{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}}
	join := func(token, uuidHex, hash string) error {
		joinToken, joinUUID, joinHash = token, uuidHex, hash
		return nil
	}

	done := make(chan error, 1)
	go func() { done <- LoginOnline(mcproto.NewConn(cConn), "localhost", 25565, session, join) }()

	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("LoginOnline: %v", err)
		}
	case <-time.After(10 * time.Second):
		t.Fatal("timeout")
	}

	if err := <-serverErr; err != nil {
		t.Fatalf("fake server: %v", err)
	}
	serverHash := <-serverHashCh

	if joinToken != "tok" {
		t.Errorf("join token = %q", joinToken)
	}
	if joinUUID != "0102030405060708090a0b0c0d0e0f10" {
		t.Errorf("join uuid = %q", joinUUID)
	}
	if joinHash != serverHash {
		t.Errorf("client hash %q != server hash %q", joinHash, serverHash)
	}
}

func fakeOnlineServer(conn *mcproto.Conn, priv *rsa.PrivateKey, der []byte, hashOut chan<- string) error {
	// Handshake + Login Start.
	if _, _, err := conn.ReadPacket(); err != nil {
		return err
	}
	if _, _, err := conn.ReadPacket(); err != nil {
		return err
	}

	// Encryption Request: serverID="", public key, verify token.
	token := []byte{0xDE, 0xAD, 0xBE, 0xEF}
	req := mcproto.AppendString(nil, "")
	req = mcproto.AppendVarInt(req, int32(len(der)))
	req = append(req, der...)
	req = mcproto.AppendVarInt(req, int32(len(token)))
	req = append(req, token...)
	if err := conn.WritePacket(pkEncryptionRequest, req); err != nil {
		return err
	}

	// Encryption Response: decrypt secret and token.
	id, data, err := conn.ReadPacket()
	if err != nil {
		return err
	}
	if id != pkEncryptionResponse {
		return errTest("unexpected packet id")
	}
	r := bytesReader(data)
	encSecret, err := readBytes(r)
	if err != nil {
		return err
	}
	encToken, err := readBytes(r)
	if err != nil {
		return err
	}
	secret, err := priv.Decrypt(rand.Reader, encSecret, nil)
	if err != nil {
		return err
	}
	gotToken, err := priv.Decrypt(rand.Reader, encToken, nil)
	if err != nil {
		return err
	}
	if !bytes.Equal(gotToken, token) {
		return errTest("verify token mismatch")
	}

	hashOut <- mcauth.AuthDigest("", secret, der)

	if err := conn.EnableEncryption(secret); err != nil {
		return err
	}

	// Login Success (encrypted): UUID + name + 0 properties.
	ok := append([]byte{}, make([]byte, 16)...)
	ok = mcproto.AppendString(ok, "Tester")
	ok = mcproto.AppendVarInt(ok, 0)
	return conn.WritePacket(pkLoginSuccess, ok)
}

type errTest string

func (e errTest) Error() string { return string(e) }
