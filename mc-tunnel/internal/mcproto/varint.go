// Package mcproto implements the small subset of the Minecraft Java Edition
// network protocol that the tunnel needs: VarInt/VarLong, length-prefixed
// packet framing with the optional compression threshold, and the CFB8
// stream cipher used after login.
//
// Reference: the community-documented protocol (wiki.vg / minecraft.wiki).
// Only primitives are implemented; nothing here depends on a Mojang account.
package mcproto

import (
	"errors"
	"io"
)

// Protocol integers are LEB128-style, 7 data bits per byte with the high bit
// as a continuation flag, encoded from the unsigned bit pattern.
const (
	maxVarIntBytes  = 5
	maxVarLongBytes = 10
	segmentBits     = 0x7F
	continueBit     = 0x80
)

var (
	// ErrVarIntTooBig is returned when a VarInt does not terminate within 5 bytes.
	ErrVarIntTooBig = errors.New("mcproto: VarInt is too big")
	// ErrVarLongTooBig is returned when a VarLong does not terminate within 10 bytes.
	ErrVarLongTooBig = errors.New("mcproto: VarLong is too big")
)

// AppendVarInt encodes value and appends it to b, returning the extended slice.
func AppendVarInt(b []byte, value int32) []byte {
	uv := uint32(value)
	for {
		if uv&^uint32(segmentBits) == 0 {
			return append(b, byte(uv))
		}
		b = append(b, byte(uv&segmentBits|continueBit))
		uv >>= 7
	}
}

// AppendVarLong encodes value and appends it to b, returning the extended slice.
func AppendVarLong(b []byte, value int64) []byte {
	uv := uint64(value)
	for {
		if uv&^uint64(segmentBits) == 0 {
			return append(b, byte(uv))
		}
		b = append(b, byte(uv&segmentBits|continueBit))
		uv >>= 7
	}
}

// VarIntLen reports how many bytes AppendVarInt would emit for value.
func VarIntLen(value int32) int {
	n := 1
	uv := uint32(value)
	for uv&^uint32(segmentBits) != 0 {
		n++
		uv >>= 7
	}
	return n
}

// ReadVarInt reads a VarInt from r one byte at a time. It returns the value
// and the number of bytes consumed.
func ReadVarInt(r io.Reader) (int32, int, error) {
	var result uint32
	var buf [1]byte
	for i := 0; ; i++ {
		if _, err := io.ReadFull(r, buf[:]); err != nil {
			return 0, i, err
		}
		b := buf[0]
		result |= uint32(b&segmentBits) << uint(7*i)
		if b&continueBit == 0 {
			return int32(result), i + 1, nil
		}
		if i+1 >= maxVarIntBytes {
			return 0, i + 1, ErrVarIntTooBig
		}
	}
}

// ReadVarLong reads a VarLong from r one byte at a time.
func ReadVarLong(r io.Reader) (int64, int, error) {
	var result uint64
	var buf [1]byte
	for i := 0; ; i++ {
		if _, err := io.ReadFull(r, buf[:]); err != nil {
			return 0, i, err
		}
		b := buf[0]
		result |= uint64(b&segmentBits) << uint(7*i)
		if b&continueBit == 0 {
			return int64(result), i + 1, nil
		}
		if i+1 >= maxVarLongBytes {
			return 0, i + 1, ErrVarLongTooBig
		}
	}
}

// AppendString encodes a length-prefixed (VarInt) UTF-8 string.
func AppendString(b []byte, s string) []byte {
	b = AppendVarInt(b, int32(len(s)))
	return append(b, s...)
}
