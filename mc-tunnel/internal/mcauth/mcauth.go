// Package mcauth implements the cryptography of Minecraft online-mode login:
// the RSA key exchange and the server-hash digest used to tell Mojang's session
// server which server a client is joining. These are the pieces that let the
// tunnel client log in as a real, paid account so the cover server can run with
// online-mode=true (indistinguishable from any legitimate player).
//
// The digest and RSA primitives are pure and test-covered; the Microsoft/Mojang
// HTTP exchange that yields an access token lives in package auth.
package mcauth

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha1"
	"crypto/x509"
	"errors"
	"fmt"
	"math/big"
)

// NewSharedSecret returns a fresh 16-byte AES-128 key for the session.
func NewSharedSecret() ([]byte, error) {
	s := make([]byte, 16)
	_, err := rand.Read(s)
	return s, err
}

// ParsePublicKey decodes the DER (PKIX) RSA public key from an Encryption
// Request packet.
func ParsePublicKey(der []byte) (*rsa.PublicKey, error) {
	pub, err := x509.ParsePKIXPublicKey(der)
	if err != nil {
		return nil, err
	}
	rp, ok := pub.(*rsa.PublicKey)
	if !ok {
		return nil, errors.New("mcauth: server public key is not RSA")
	}
	return rp, nil
}

// Encrypt RSA/PKCS#1 v1.5 encrypts data (the shared secret or verify token)
// with the server's public key, as the Encryption Response requires.
func Encrypt(pub *rsa.PublicKey, data []byte) ([]byte, error) {
	return rsa.EncryptPKCS1v15(rand.Reader, pub, data)
}

// AuthDigest computes the Minecraft server-hash: SHA-1 over the server id, the
// shared secret and the server's public key, rendered as a signed, two's
// complement, big-endian hex string with no leading zeros. This is the serverId
// sent to sessionserver.mojang.com/join.
func AuthDigest(serverID string, sharedSecret, pubKeyDER []byte) string {
	h := sha1.New()
	h.Write([]byte(serverID))
	h.Write(sharedSecret)
	h.Write(pubKeyDER)
	return minecraftHex(h.Sum(nil))
}

// minecraftHex renders a 20-byte SHA-1 sum the way Minecraft does: as a signed
// two's complement integer in hex. High bit set => negative, printed with a
// leading '-' and no leading zeros.
func minecraftHex(sum []byte) string {
	negative := len(sum) > 0 && sum[0]&0x80 != 0
	i := new(big.Int).SetBytes(sum)
	if negative {
		max := new(big.Int).Lsh(big.NewInt(1), uint(len(sum))*8)
		i.Sub(i, max)
	}
	return fmt.Sprintf("%x", i)
}
