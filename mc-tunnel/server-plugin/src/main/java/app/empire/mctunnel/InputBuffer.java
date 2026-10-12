package app.empire.mctunnel;

import java.io.EOFException;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.util.ArrayDeque;

/**
 * A thread-safe byte pipe: producers append chunks without blocking, one
 * consumer reads a byte stream and blocks for more. Used both for the raw
 * inbound channel bytes (parsed into frames) and for each stream's client->
 * socket data. Memory stays bounded in practice because the credit window caps
 * how much the peer sends before the consumer drains and acknowledges.
 */
final class InputBuffer {
    private final ArrayDeque<byte[]> queue = new ArrayDeque<>();
    private byte[] cur;
    private int pos;
    private boolean closed;

    synchronized void append(byte[] b) {
        if (closed || b.length == 0) {
            return;
        }
        queue.add(b);
        notifyAll();
    }

    synchronized void close() {
        closed = true;
        notifyAll();
    }

    private boolean ensure() throws IOException {
        while (cur == null || pos >= cur.length) {
            if (!queue.isEmpty()) {
                cur = queue.poll();
                pos = 0;
                continue;
            }
            if (closed) {
                return false;
            }
            try {
                wait();
            } catch (InterruptedException e) {
                throw new InterruptedIOException();
            }
        }
        return true;
    }

    /** Reads exactly dst.length bytes or throws EOFException. */
    synchronized void readFully(byte[] dst) throws IOException {
        int off = 0;
        while (off < dst.length) {
            if (!ensure()) {
                throw new EOFException();
            }
            int take = Math.min(dst.length - off, cur.length - pos);
            System.arraycopy(cur, pos, dst, off, take);
            pos += take;
            off += take;
        }
    }

    /** Reads one byte, or -1 at end of stream. */
    synchronized int readByte() throws IOException {
        if (!ensure()) {
            return -1;
        }
        return cur[pos++] & 0xff;
    }

    /** Reads up to dst.length bytes, blocking for at least one; -1 at end. */
    synchronized int read(byte[] dst) throws IOException {
        if (!ensure()) {
            return -1;
        }
        int take = Math.min(dst.length, cur.length - pos);
        System.arraycopy(cur, pos, dst, 0, take);
        pos += take;
        return take;
    }
}
