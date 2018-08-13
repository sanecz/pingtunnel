import socket
import struct

ICMP_ECHO = 0
ICMP_ECHO_REQUEST = 8

class ICMPPacket(object):
    def __init__(self, type, code, checksum, id,
                 sequence, data, source_ip, dest=(None, None)):
        self.type, self.code, self.checksum = type, code, checksum
        self.id, self.sequence, self.data = id, sequence, data
        self.dest = dest
        self.source_ip = source_ip
        self.length = len(self.data)

    def __repr__(self):
        return "<ICMP packet: type = {s.type}, code = {s.code}, " \
            "data length = {length}".format(s=self, length=len(self.data))

    def __str__(self):
        return "Type of message: {s.type}, Code {s.code},"\
            "Checksum: {s.checksum}, ID: {s.id}, Sequence: {s.sequence}, " \
            "Data: {s.data}, Data length: {length}".format(s=self, length=len(self.data))

    def create(self):
        pack_str = "!BBHHH4sH"
        pack_args = [self.type, self.code, 0, self.id, self.sequence,
                     socket.inet_aton(self.dest[0]), self.dest[1]]

        if self.length:
            pack_str += "{}s".format(self.length)
            pack_args.append(self.data)

        self.checksum = self._checksum(struct.pack(pack_str, *pack_args)) 
        pack_args[2] = self.checksum
        return struct.pack(pack_str, *pack_args)

    @classmethod
    def parse(cls, packet):
        ip_pack_str = "BBHHHBBH4s4s"
        icmp_pack_str = "!BBHHH4sH"
        data = ""

        ip_packet, icmp_packet = packet[:20], packet[20:] # split ip header

        ip_packet = struct.unpack(ip_pack_str, ip_packet)

        source_ip = ip_packet[8]
        icmp_pack_len = struct.calcsize(icmp_pack_str)
        packet_len = len(icmp_packet) - icmp_pack_len

        if packet_len > 0:
            icmp_data_str = "{}s".format(packet_len)
            data = struct.unpack(icmp_data_str, icmp_packet[icmp_pack_len:])[0]

        type, code, checksum, id, sequence, dest_ip, \
            dest_port = struct.unpack(icmp_pack_str, icmp_packet[:icmp_pack_len])

        return cls(type, code, checksum, id, sequence, data,
                   socket.inet_ntoa(source_ip),
                   (socket.inet_ntoa(dest_ip), dest_port))


    @staticmethod
    def _checksum(packet):
        csum = 0
        countTo = (len(packet) / 2) * 2
        count = 0

        while count < countTo:
            thisVal = ord(packet[count+1]) * 256 + ord(packet[count])
            csum = csum + thisVal
            csum = csum & 0xffffffffL
            count = count + 2

        if countTo < len(packet):
            csum = csum + ord(packet[len(packet) - 1])
            csum = csum & 0xffffffffL

        csum = (csum >> 16) + (csum & 0xffff)
        csum = csum + (csum >> 16)
        checksum = ~csum
        checksum = checksum & 0xffff
        checksum = checksum >> 8 | (checksum << 8 & 0xff00)
        return checksum
