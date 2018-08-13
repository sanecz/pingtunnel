import argparse
import icmp
import select
import socket
import threading

TCP_BUFFER_SIZE = 2 ** 10
ICMP_BUFFER_SIZE = 65565

PROGNAME="pptunnel"

class Tunnel(object):
    @staticmethod
    def create_icmp_socket():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        except socket.error as e:
            raise
        return sock

    @staticmethod
    def create_tcp_socket(dest, server=False):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(dest) if server else sock.connect(dest)
        except socket.error as e:
            raise
        return sock

    def icmp_data_handler(self, sock):
        raise NotImplementedError

    def tcp_data_handler(self, sock):
        raise NotImplementedError

    def run(self):
        while True:
            sread, _, _ = select.select(self.sockets, [], [])
            for sock in sread:
                if sock.proto == socket.IPPROTO_ICMP:
                    self.icmp_data_handler(sock)
                else:
                    self.tcp_data_handler(sock)

class Server(Tunnel):
    def __init__(self):
        self.tcp_socket = None
        self.source, self.dest = None, None
        self.icmp_socket = self.create_icmp_socket()
        self.sockets = [self.icmp_socket]

    def icmp_data_handler(self, sock):
        packet, addr = self.icmp_socket.recvfrom(ICMP_BUFFER_SIZE)
        try:
            packet = icmp.ICMPPacket.parse(packet)
        except ValueError:
            print "Malformated packet"
            return
        self.source = addr[0]
        self.dest = packet.dest
        if packet.type == icmp.ICMP_ECHO and packet.code == 0:
            # our packet, do nothing
            pass
        elif packet.type == icmp.ICMP_ECHO_REQUEST and packet.code == 1:
            # control
            self.sockets.remove(self.tcp_socket)
            self.tcp_socket.close()
            self.tcp_socket = None
        else:
            if not self.tcp_socket:
                self.tcp_socket = self.create_tcp_socket(self.dest)
                self.sockets.append(self.tcp_socket)
            self.tcp_socket.send(packet.data)

    def tcp_data_handler(self, sock):
        sdata = sock.recv(TCP_BUFFER_SIZE)
        new_packet = icmp.ICMPPacket(icmp.ICMP_ECHO, 0, 0, 0, 0,
                                     sdata, self.source, self.dest)
        packet = new_packet.create()
        self.icmp_socket.sendto(packet, (self.source, 0))



class ProxyClient(Tunnel, threading.Thread):
    def __init__(self, proxy, sock, dest):
        threading.Thread.__init__(self)
        self.proxy = proxy
        self.dest = dest
        self.tcp_socket = sock
        self.icmp_socket = self.create_icmp_socket()
        self.sockets = [self.tcp_socket, self.icmp_socket]

    def icmp_data_handler(self, sock):
        sdata = sock.recvfrom(ICMP_BUFFER_SIZE)
        try:
            packet = icmp.ICMPPacket.parse(sdata[0])
        except ValueError:
            # Bad packet, malformated, not our, EOF etc..
            return
        if packet.type != icmp.ICMP_ECHO_REQUEST:
            self.tcp_socket.send(packet.data)

    def tcp_data_handler(self, sock):
        sdata = sock.recv(TCP_BUFFER_SIZE)
        # if no data the socket may be closed/timeout/EOF
        len_sdata = len(sdata)
        code = 0 if len_sdata > 0 else 1
        new_packet = icmp.ICMPPacket(
            icmp.ICMP_ECHO_REQUEST, code, 0, 0, 0,
            sdata, self.tcp_socket.getsockname(), self.dest)
        packet = new_packet.create()
        self.icmp_socket.sendto(packet, (self.proxy, 1))
        if code == 1:
            exit() #exit thread


class Proxy(ProxyClient):
    def __init__(self, proxy, local_host, local_port, dest_host, dest_port):
        self.proxy = proxy
        self.local = (local_host, local_port)
        self.dest = (dest_host, dest_port)
        self.tcp_server_socket = self.create_tcp_socket(self.local, server=True)

    def run(self):
        while True:
            self.tcp_server_socket.listen(5)
            sock, addr = self.tcp_server_socket.accept()
            newthread = ProxyClient(self.proxy, sock, self.dest)
            newthread.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="pptunnel, python ping tunnel, send your tcp traffic over icmp",
        usage="""Needs to be runned as root (use of raw sockets)
  Client side: pptunnel -p <proxy_host> -lp <proxy_port> -dh <dest_host> -dp <dest_port>
  Proxy side: pptunnel -s""",
        epilog="""
Example:
We want to connect in ftp to google.com:21 via our server proxy.server.com
  Client : sudo python pptunnel -p proxy.server.com -lp 8000 -dh google.com -dp 21
  Proxy  : sudo python pptunnel -s 
  Client : ftp localhost 8000"""
    )

    parser.add_argument("-s", "--server", action="store_true", default=False,
                        help="Set proxy mode")
    parser.add_argument("-p", "--proxy_host",
                        help="Host on which the proxy is running")
    parser.add_argument("-lh", "--local_host", default="127.0.0.1",
                        help="(local) Listen ip for incomming TCP connections,"\
                        "default 127.0.0.1")
    parser.add_argument("-lp", "--local_port", type=int,
                        help="(local) Listen port for incomming TCP connections")
    parser.add_argument("-dh", "--destination_host",
                        help="Specifies the remote host to send your TCP connection")
    parser.add_argument("-dp", "--destination_port", type=int,
                        help="Specifies the remote port to send your TCP connection")

    args = parser.parse_args()

    if args.server:
        tunnel = Server()
    else:
        tunnel = Proxy(
            proxy=args.proxy_host,
            local_host=args.local_host, local_port=args.local_port,
            dest_host=args.destination_host, dest_port=args.destination_port
        )

    tunnel.run()
