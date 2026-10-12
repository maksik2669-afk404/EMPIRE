package app.empire.mctunnel;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;

/**
 * Parses the connect header a client writes at the start of each stream. The
 * encoding mirrors internal/mctun/dial.go: [ver=1][atyp][addr...][port:2],
 * with SOCKS5-style address types (1=IPv4, 3=domain, 4=IPv6).
 */
final class DialHeader {
    private static final int VERSION = 1;
    private static final int ATYP_IPV4 = 1;
    private static final int ATYP_DOMAIN = 3;
    private static final int ATYP_IPV6 = 4;

    private DialHeader() {
    }

    /** Reads a target address, returned unresolved so DNS happens at connect. */
    static InetSocketAddress read(InputBuffer in) throws IOException {
        int ver = in.readByte();
        if (ver != VERSION) {
            throw new IOException("bad dial version " + ver);
        }
        int atyp = in.readByte();
        String host;
        switch (atyp) {
            case ATYP_IPV4 -> host = readIp(in, 4);
            case ATYP_IPV6 -> host = readIp(in, 16);
            case ATYP_DOMAIN -> {
                int len = in.readByte();
                if (len < 0) {
                    throw new IOException("truncated domain length");
                }
                byte[] b = new byte[len];
                in.readFully(b);
                host = new String(b, java.nio.charset.StandardCharsets.US_ASCII);
            }
            default -> throw new IOException("bad address type " + atyp);
        }
        int hi = in.readByte();
        int lo = in.readByte();
        if (hi < 0 || lo < 0) {
            throw new IOException("truncated port");
        }
        return InetSocketAddress.createUnresolved(host, (hi << 8) | lo);
    }

    private static String readIp(InputBuffer in, int n) throws IOException {
        byte[] b = new byte[n];
        in.readFully(b);
        return InetAddress.getByAddress(b).getHostAddress();
    }
}
