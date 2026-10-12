package mcproto

import (
	"bytes"
	"testing"
)

func TestVarIntRoundTrip(t *testing.T) {
	cases := []int32{0, 1, 2, 127, 128, 255, 256, 2147483647, -1, -2147483648, 25565}
	for _, v := range cases {
		b := AppendVarInt(nil, v)
		if len(b) != VarIntLen(v) {
			t.Fatalf("VarIntLen(%d)=%d, encoded %d bytes", v, VarIntLen(v), len(b))
		}
		got, n, err := ReadVarInt(bytes.NewReader(b))
		if err != nil {
			t.Fatalf("ReadVarInt(%d): %v", v, err)
		}
		if got != v || n != len(b) {
			t.Fatalf("VarInt %d: got %d (n=%d), encoded=%v", v, got, n, b)
		}
	}
}

// Known encodings from the protocol documentation.
func TestVarIntKnownVectors(t *testing.T) {
	vectors := map[int32][]byte{
		0:          {0x00},
		1:          {0x01},
		127:        {0x7f},
		128:        {0x80, 0x01},
		255:        {0xff, 0x01},
		2147483647: {0xff, 0xff, 0xff, 0xff, 0x07},
		-1:         {0xff, 0xff, 0xff, 0xff, 0x0f},
	}
	for v, want := range vectors {
		if got := AppendVarInt(nil, v); !bytes.Equal(got, want) {
			t.Errorf("AppendVarInt(%d)=%v, want %v", v, got, want)
		}
	}
}

func TestVarIntTooBig(t *testing.T) {
	bad := []byte{0x80, 0x80, 0x80, 0x80, 0x80, 0x01}
	if _, _, err := ReadVarInt(bytes.NewReader(bad)); err != ErrVarIntTooBig {
		t.Fatalf("got %v, want ErrVarIntTooBig", err)
	}
}

func TestVarLongRoundTrip(t *testing.T) {
	cases := []int64{0, 1, 127, 128, 9223372036854775807, -1, -9223372036854775808}
	for _, v := range cases {
		b := AppendVarLong(nil, v)
		got, n, err := ReadVarLong(bytes.NewReader(b))
		if err != nil {
			t.Fatalf("ReadVarLong(%d): %v", v, err)
		}
		if got != v || n != len(b) {
			t.Fatalf("VarLong %d: got %d (n=%d)", v, got, n)
		}
	}
}

func TestAppendString(t *testing.T) {
	b := AppendString(nil, "hello")
	want := append([]byte{0x05}, "hello"...)
	if !bytes.Equal(b, want) {
		t.Fatalf("AppendString=%v, want %v", b, want)
	}
}
