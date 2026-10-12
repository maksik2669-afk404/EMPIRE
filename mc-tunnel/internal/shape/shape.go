// Package shape governs how tunnel bytes are sized and paced onto the Minecraft
// link. It exists because the destination (a real server) only defeats active
// probing and IP-reputation blocking; a passive DPI box classifies on the
// *statistics* of the flow — packet sizes, cadence, burstiness. A bulk transfer
// does not look like gameplay no matter where it goes.
//
// Honest scope: this package caps throughput and randomizes packet sizes, which
// removes the most obvious tells (uniform MTU-sized packets, download-shaped
// bursts). It does NOT yet reproduce the temporal distribution of real
// Minecraft play. Faithfully matching that distribution is the hard, open part
// of the problem and the thing a serious censor ultimately measures; treat this
// as a necessary floor, not a finished disguise.
package shape

import (
	"math/rand"
	"sync"
	"time"
)

// Limiter is a token bucket measured in bytes. It smooths the tunnel's output
// rate to a configured ceiling so throughput never spikes into a download
// profile.
type Limiter struct {
	mu     sync.Mutex
	rate   float64 // bytes per second
	burst  float64 // bucket capacity
	tokens float64
	last   time.Time
	now    func() time.Time
	sleep  func(time.Duration)
}

// NewLimiter builds a limiter allowing ratePerSec bytes/second with a bucket of
// burst bytes (the most that may be sent back-to-back).
func NewLimiter(ratePerSec, burst int) *Limiter {
	return &Limiter{
		rate:   float64(ratePerSec),
		burst:  float64(burst),
		tokens: float64(burst),
		last:   time.Now(),
		now:    time.Now,
		sleep:  time.Sleep,
	}
}

// Wait blocks until n bytes of budget are available, then consumes them. n is
// clamped to the burst size so a single large write cannot deadlock.
func (l *Limiter) Wait(n int) {
	l.mu.Lock()
	need := float64(n)
	if need > l.burst {
		need = l.burst
	}
	for {
		now := l.now()
		l.tokens += l.rate * now.Sub(l.last).Seconds()
		if l.tokens > l.burst {
			l.tokens = l.burst
		}
		l.last = now
		if l.tokens >= need {
			l.tokens -= need
			l.mu.Unlock()
			return
		}
		deficit := need - l.tokens
		wait := time.Duration(deficit / l.rate * float64(time.Second))
		l.mu.Unlock()
		l.sleep(wait)
		l.mu.Lock()
	}
}

// Split breaks data into chunks whose sizes are drawn uniformly from
// [minSize, maxSize], so observed packet sizes vary instead of pinning to the
// link MTU. The final chunk carries the remainder and may be shorter than
// minSize. Concatenating the result reproduces data exactly.
func Split(data []byte, minSize, maxSize int, rng *rand.Rand) [][]byte {
	if minSize < 1 {
		minSize = 1
	}
	if maxSize < minSize {
		maxSize = minSize
	}
	var chunks [][]byte
	for len(data) > 0 {
		size := minSize + rng.Intn(maxSize-minSize+1)
		if size > len(data) {
			size = len(data)
		}
		chunks = append(chunks, data[:size])
		data = data[size:]
	}
	return chunks
}
