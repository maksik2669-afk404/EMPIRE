package app.empire.mctunnel;

import java.io.IOException;
import java.io.OutputStream;

/**
 * One multiplexed stream on the server side. Client->socket data arrives via
 * push() and is drained to the socket; socket->client data is sent with
 * writeToClient(), which respects the credit window the client advertises.
 */
final class SrvStream {
    private final int id;
    private final PlayerTunnel tunnel;
    final InputBuffer inbound = new InputBuffer(); // client -> socket bytes

    private final Object sendLock = new Object();
    private int sendWindow = TunnelPlugin.INITIAL_WINDOW;
    private volatile boolean dead;

    SrvStream(int id, PlayerTunnel tunnel) {
        this.id = id;
        this.tunnel = tunnel;
    }

    int id() {
        return id;
    }

    void push(byte[] data) {
        inbound.append(data);
    }

    void addSendWindow(int n) {
        synchronized (sendLock) {
            sendWindow += n;
            sendLock.notifyAll();
        }
    }

    void die() {
        dead = true;
        inbound.close();
        synchronized (sendLock) {
            sendLock.notifyAll();
        }
    }

    /** Pumps everything from the socket to the client, honoring the window. */
    void pumpSocketToClient(java.io.InputStream sock) throws IOException {
        byte[] buf = new byte[TunnelPlugin.MAX_FRAME];
        while (!dead) {
            int n = sock.read(buf);
            if (n < 0) {
                return;
            }
            int off = 0;
            while (off < n) {
                int grant;
                synchronized (sendLock) {
                    while (sendWindow == 0 && !dead) {
                        try {
                            sendLock.wait();
                        } catch (InterruptedException e) {
                            return;
                        }
                    }
                    if (dead) {
                        return;
                    }
                    grant = Math.min(n - off, sendWindow);
                    if (grant > TunnelPlugin.MAX_FRAME) {
                        grant = TunnelPlugin.MAX_FRAME;
                    }
                    sendWindow -= grant;
                }
                byte[] slice = new byte[grant];
                System.arraycopy(buf, off, slice, 0, grant);
                tunnel.writeFrame(TunnelPlugin.CMD_PSH, id, slice);
                off += grant;
            }
        }
    }

    /** Pumps everything from the client (inbound) to the socket, acking credit. */
    void pumpClientToSocket(OutputStream sock) throws IOException {
        byte[] buf = new byte[16 * 1024];
        while (!dead) {
            int n = inbound.read(buf);
            if (n < 0) {
                return;
            }
            sock.write(buf, 0, n);
            sock.flush();
            // Return credit so the client may send n more bytes.
            byte[] credit = new byte[4];
            credit[0] = (byte) (n >>> 24);
            credit[1] = (byte) (n >>> 16);
            credit[2] = (byte) (n >>> 8);
            credit[3] = (byte) n;
            tunnel.writeFrame(TunnelPlugin.CMD_WND, id, credit);
        }
    }
}
