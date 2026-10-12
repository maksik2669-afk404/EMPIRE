package shape

import (
	"bytes"
	"math/rand"
	"testing"
	"time"
)

func TestSplitReassembles(t *testing.T) {
	rng := rand.New(rand.NewSource(1))
	for _, n := range []int{0, 1, 10, 500, 70000} {
		data := make([]byte, n)
		rng.Read(data)
		chunks := Split(data, 40, 1200, rng)
		var buf bytes.Buffer
		for i, c := range chunks {
			if len(c) > 1200 {
				t.Fatalf("chunk %d size %d > max", i, len(c))
			}
			// Every chunk but the last must respect the minimum.
			if i < len(chunks)-1 && len(c) < 40 {
				t.Fatalf("chunk %d size %d < min", i, len(c))
			}
			buf.Write(c)
		}
		if !bytes.Equal(buf.Bytes(), data) {
			t.Fatalf("n=%d: reassembly mismatch", n)
		}
	}
}

// TestLimiterRate drives the limiter against a virtual clock and checks that a
// transfer is paced to roughly the configured rate.
func TestLimiterRate(t *testing.T) {
	var vnow time.Duration
	l := NewLimiter(1000, 100) // 1000 B/s, burst 100
	l.now = func() time.Time { return time.Unix(0, int64(vnow)) }
	l.sleep = func(d time.Duration) { vnow += d }
	l.last = l.now()
	l.tokens = 100

	// Send 1100 bytes in 100-byte writes. After the initial burst of 100,
	// the remaining 1000 bytes must take ~1s at 1000 B/s.
	for i := 0; i < 11; i++ {
		l.Wait(100)
	}
	got := time.Duration(vnow).Seconds()
	if got < 0.95 || got > 1.05 {
		t.Fatalf("elapsed %.3fs, want ~1.0s", got)
	}
}
