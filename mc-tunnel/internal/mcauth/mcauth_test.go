package mcauth

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"testing"
)

// Canonical Minecraft server-hash vectors (the famous Notch/jeb_/simon cases
// from the protocol documentation). They pin the signed two's-complement hex.
func TestMinecraftHexVectors(t *testing.T) {
	cases := map[string]string{
		"Notch": "4ed1f46bbe04bc756bcb17c0c7ce3e4632f06a48",
		"jeb_":  "-7c9d5b0044c130109a5d7b5fb5c317c02b4e28c1",
		"simon": "88e16a1019277b15d58faf0541e11910eb756f6",
	}
	for in, want := range cases {
		// AuthDigest with empty secret/key hashes just the input string.
		if got := AuthDigest(in, nil, nil); got != want {
			t.Errorf("AuthDigest(%q)=%s, want %s", in, got, want)
		}
	}
}

func TestRSARoundTrip(t *testing.T) {
	priv, err := rsa.GenerateKey(rand.Reader, 1024)
	if err != nil {
		t.Fatal(err)
	}
	der, err := x509.MarshalPKIXPublicKey(&priv.PublicKey)
	if err != nil {
		t.Fatal(err)
	}
	pub, err := ParsePublicKey(der)
	if err != nil {
		t.Fatal(err)
	}
	secret, err := NewSharedSecret()
	if err != nil {
		t.Fatal(err)
	}
	ct, err := Encrypt(pub, secret)
	if err != nil {
		t.Fatal(err)
	}
	pt, err := rsa.DecryptPKCS1v15(rand.Reader, priv, ct)
	if err != nil {
		t.Fatal(err)
	}
	if string(pt) != string(secret) {
		t.Fatal("decrypted secret does not match")
	}
}

func TestParsePublicKeyRejectsGarbage(t *testing.T) {
	if _, err := ParsePublicKey([]byte("not a key")); err == nil {
		t.Fatal("expected error on garbage key")
	}
}
