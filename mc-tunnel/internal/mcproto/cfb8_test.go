package mcproto

import (
	"bytes"
	"crypto/aes"
	"crypto/rand"
	"testing"
)

func TestCFB8RoundTrip(t *testing.T) {
	secret := make([]byte, 16)
	rand.Read(secret)
	block, err := aes.NewCipher(secret)
	if err != nil {
		t.Fatal(err)
	}
	enc := newCFB8(block, secret, false)
	dec := newCFB8(block, secret, true)

	plain := make([]byte, 1000)
	rand.Read(plain)

	// Encrypt byte-fragmented to prove the feedback register survives arbitrary
	// chunking (the real stream never aligns to packet boundaries).
	ct := make([]byte, len(plain))
	for i := 0; i < len(plain); i += 7 {
		j := i + 7
		if j > len(plain) {
			j = len(plain)
		}
		enc.XORKeyStream(ct[i:j], plain[i:j])
	}
	got := make([]byte, len(ct))
	dec.XORKeyStream(got, ct)

	if bytes.Equal(ct, plain) {
		t.Fatal("ciphertext equals plaintext")
	}
	if !bytes.Equal(got, plain) {
		t.Fatal("decrypt did not recover plaintext")
	}
}
