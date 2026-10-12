package app.empire.mctunnel;

import org.bukkit.Bukkit;
import org.bukkit.entity.Player;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Per-player demultiplexer. Raw channel bytes feed a single frame parser; each
 * SYN opens a worker that reads the dial header, connects the real socket, and
 * bridges it to the stream. Outgoing frames from all streams are serialized
 * through writeFrame() and chunked back onto the channel on the main thread.
 */
final class PlayerTunnel {
    private final TunnelPlugin plugin;
    private final Player player;
    private final InputBuffer inbound = new InputBuffer();
    private final Map<Integer, SrvStream> streams = new ConcurrentHashMap<>();
    private final Object sendSerial = new Object();
    private volatile boolean closed;

    PlayerTunnel(TunnelPlugin plugin, Player player) {
        this.plugin = plugin;
        this.player = player;
        Thread parser = new Thread(this::parseLoop, "mctunnel-parse-" + player.getName());
        parser.setDaemon(true);
        parser.start();
    }

    void onBytes(byte[] b) {
        inbound.append(b);
    }

    private void parseLoop() {
        try {
            byte[] header = new byte[TunnelPlugin.HEADER];
            while (!closed) {
                inbound.readFully(header);
                int cmd = header[0] & 0xff;
                int sid = be32(header, 1);
                int len = ((header[5] & 0xff) << 8) | (header[6] & 0xff);
                byte[] data = new byte[len];
                if (len > 0) {
                    inbound.readFully(data);
                }
                dispatch(cmd, sid, data);
            }
        } catch (IOException e) {
            // Channel closed or malformed; tear everything down.
        } finally {
            close();
        }
    }

    private void dispatch(int cmd, int sid, byte[] data) {
        switch (cmd) {
            case TunnelPlugin.CMD_SYN -> openStream(sid);
            case TunnelPlugin.CMD_PSH -> {
                SrvStream s = streams.get(sid);
                if (s != null) {
                    s.push(data);
                }
            }
            case TunnelPlugin.CMD_WND -> {
                SrvStream s = streams.get(sid);
                if (s != null && data.length == 4) {
                    s.addSendWindow(be32(data, 0));
                }
            }
            case TunnelPlugin.CMD_FIN -> {
                SrvStream s = streams.remove(sid);
                if (s != null) {
                    s.die();
                }
            }
            case TunnelPlugin.CMD_NOP -> {
            }
            default -> {
            }
        }
    }

    private void openStream(int sid) {
        SrvStream stream = new SrvStream(sid, this);
        streams.put(sid, stream);
        plugin.pool().submit(() -> runStream(stream));
    }

    private void runStream(SrvStream stream) {
        Socket sock = null;
        try {
            InetSocketAddress target = DialHeader.read(stream.inbound);
            sock = new Socket();
            sock.connect(new InetSocketAddress(target.getHostString(), target.getPort()),
                    plugin.dialTimeoutMs());

            final Socket fsock = sock;
            Thread up = new Thread(() -> {
                try {
                    stream.pumpSocketToClient(fsock.getInputStream());
                } catch (IOException ignored) {
                } finally {
                    closeStream(stream, fsock);
                }
            }, "mctunnel-up-" + stream.id());
            up.setDaemon(true);
            up.start();

            stream.pumpClientToSocket(sock.getOutputStream());
        } catch (IOException | RuntimeException e) {
            // connect failed or header malformed
        } finally {
            closeStream(stream, sock);
        }
    }

    private void closeStream(SrvStream stream, Socket sock) {
        if (streams.remove(stream.id()) != null) {
            writeFrame(TunnelPlugin.CMD_FIN, stream.id(), new byte[0]);
        }
        stream.die();
        if (sock != null) {
            try {
                sock.close();
            } catch (IOException ignored) {
            }
        }
    }

    /** Serializes a frame onto the channel and chunks it back to the player. */
    void writeFrame(int cmd, int sid, byte[] data) {
        if (closed) {
            return;
        }
        byte[] frame = new byte[TunnelPlugin.HEADER + data.length];
        frame[0] = (byte) cmd;
        frame[1] = (byte) (sid >>> 24);
        frame[2] = (byte) (sid >>> 16);
        frame[3] = (byte) (sid >>> 8);
        frame[4] = (byte) sid;
        frame[5] = (byte) (data.length >>> 8);
        frame[6] = (byte) data.length;
        System.arraycopy(data, 0, frame, TunnelPlugin.HEADER, data.length);

        synchronized (sendSerial) {
            for (int off = 0; off < frame.length; off += TunnelPlugin.MAX_MESSAGE) {
                int end = Math.min(frame.length, off + TunnelPlugin.MAX_MESSAGE);
                byte[] chunk = new byte[end - off];
                System.arraycopy(frame, off, chunk, 0, chunk.length);
                sendChunk(chunk);
            }
        }
    }

    private void sendChunk(byte[] chunk) {
        // Bukkit messaging is not thread-safe; send on the main thread. Tasks
        // run in submission order, preserving the channel byte stream.
        Bukkit.getScheduler().runTask(plugin, () -> {
            if (player.isOnline()) {
                player.sendPluginMessage(plugin, plugin.channel(), chunk);
            }
        });
    }

    void close() {
        if (closed) {
            return;
        }
        closed = true;
        inbound.close();
        for (SrvStream s : streams.values()) {
            s.die();
        }
        streams.clear();
        plugin.forget(player.getUniqueId());
    }

    private static int be32(byte[] b, int off) {
        return ((b[off] & 0xff) << 24) | ((b[off + 1] & 0xff) << 16)
                | ((b[off + 2] & 0xff) << 8) | (b[off + 3] & 0xff);
    }
}
