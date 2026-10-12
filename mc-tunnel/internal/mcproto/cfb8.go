package mcproto

import "crypto/cipher"

// cfb8 implements the AES/CFB8 stream cipher that Minecraft uses for the
// post-login stream. Go's standard library dropped general CFB and never had
// the 8-bit feedback variant, so we implement it directly. One byte of
// keystream is produced per block encryption; the feedback register always
// takes the ciphertext byte, in both directions.
type cfb8 struct {
	block    cipher.Block
	register []byte
	tmp      []byte
	decrypt  bool
}

func newCFB8(block cipher.Block, iv []byte, decrypt bool) *cfb8 {
	bs := block.BlockSize()
	reg := make([]byte, bs)
	copy(reg, iv)
	return &cfb8{
		block:    block,
		register: reg,
		tmp:      make([]byte, bs),
		decrypt:  decrypt,
	}
}

func (c *cfb8) XORKeyStream(dst, src []byte) {
	if len(dst) < len(src) {
		panic("mcproto: cfb8 output smaller than input")
	}
	bs := len(c.register)
	for i := range src {
		c.block.Encrypt(c.tmp, c.register)
		out := src[i] ^ c.tmp[0]
		feedback := out
		if c.decrypt {
			feedback = src[i]
		}
		dst[i] = out
		copy(c.register, c.register[1:])
		c.register[bs-1] = feedback
	}
}
