package app.empire.mctunnel;

import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.plugin.messaging.PluginMessageListener;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * McTunnel bridges a private Minecraft plugin channel to the open internet,
 * acting as the exit side of the mc-tunnel transport. A companion client logs
 * in as an ordinary player and multiplexes its proxied connections over the
 * channel; this plugin demultiplexes them and opens the real outbound sockets.
 *
 * The wire format mirrors internal/mux and internal/mctun on the Go side:
 * length-delimited frames (cmd, streamId, len) carried as the raw byte stream
 * of the channel's plugin messages, with a per-stream credit window.
 *
 * Only stable Bukkit messaging APIs are used, so no Minecraft protocol packet
 * IDs appear here and the plugin is version-independent across the 1.20+ line.
 */
public final class TunnelPlugin extends JavaPlugin implements Listener, PluginMessageListener {

    static final int CMD_SYN = 1, CMD_PSH = 2, CMD_FIN = 3, CMD_NOP = 4, CMD_WND = 5;
    static final int HEADER = 7;
    static final int MAX_FRAME = 65535;
    static final int INITIAL_WINDOW = 256 * 1024;
    static final int MAX_MESSAGE = 1024; // split outgoing stream into chunks this big

    private String channel;
    private int dialTimeoutMs;
    private final Map<UUID, PlayerTunnel> tunnels = new ConcurrentHashMap<>();
    private ExecutorService pool;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        channel = getConfig().getString("channel", "mctunnel:d");
        dialTimeoutMs = getConfig().getInt("dial-timeout-ms", 10000);
        pool = Executors.newCachedThreadPool(r -> {
            Thread t = new Thread(r, "mctunnel-worker");
            t.setDaemon(true);
            return t;
        });
        getServer().getMessenger().registerIncomingPluginChannel(this, channel, this);
        getServer().getMessenger().registerOutgoingPluginChannel(this, channel);
        getServer().getPluginManager().registerEvents(this, this);
        getLogger().info("McTunnel active on channel '" + channel + "'");
    }

    @Override
    public void onDisable() {
        for (PlayerTunnel t : tunnels.values()) {
            t.close();
        }
        tunnels.clear();
        if (pool != null) {
            pool.shutdownNow();
        }
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        PlayerTunnel t = tunnels.remove(e.getPlayer().getUniqueId());
        if (t != null) {
            t.close();
        }
    }

    @Override
    public void onPluginMessageReceived(String ch, Player player, byte[] message) {
        if (!ch.equals(channel)) {
            return; // not ours — behave like a server that ignores unknown mods
        }
        PlayerTunnel t = tunnels.computeIfAbsent(player.getUniqueId(),
                k -> new PlayerTunnel(this, player));
        t.onBytes(message);
    }

    ExecutorService pool() {
        return pool;
    }

    int dialTimeoutMs() {
        return dialTimeoutMs;
    }

    String channel() {
        return channel;
    }

    void forget(UUID id) {
        tunnels.remove(id);
    }
}
