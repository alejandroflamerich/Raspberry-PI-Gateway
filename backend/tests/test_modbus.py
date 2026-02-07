import struct
import socket
from app.modules.sw.modbus import TcpModbusClient


class FakeSocket:
    def __init__(self, *args, **kwargs):
        self._recv_queue = []
        self.sent = b""

    def settimeout(self, t):
        pass

    def connect(self, addr):
        pass

    def sendall(self, data: bytes):
        # store sent packet and prepare a response based on transaction id and request
        self.sent += data
        # transaction id in first 2 bytes
        tid = struct.unpack(">H", data[0:2])[0]
        unit = data[6]
        pdu = data[7:]
        func = pdu[0]
        if func == 3:
            # parse address/count
            address = struct.unpack(">H", pdu[1:3])[0]
            count = struct.unpack(">H", pdu[3:5])[0]
            byte_count = count * 2
            # generate sample registers: 1..count
            registers = b"".join(struct.pack(">H", i + 1) for i in range(count))
            resp_pdu = struct.pack(">BB", 3, byte_count) + registers
            length = len(resp_pdu) + 1
            hdr = struct.pack(">HHHB", tid, 0, length, unit)
            self._recv_queue = [hdr, resp_pdu]

    def recv(self, n: int) -> bytes:
        if not self._recv_queue:
            return b""
        part = self._recv_queue[0][:n]
        self._recv_queue[0] = self._recv_queue[0][n:]
        if len(self._recv_queue[0]) == 0:
            self._recv_queue.pop(0)
        return part

    def close(self):
        pass


def test_read_holding_registers_monkeypatch(monkeypatch):
    # replace socket.socket with FakeSocket
    import socket as _socket

    monkeypatch.setattr(_socket, "socket", lambda *a, **k: FakeSocket())

    client = TcpModbusClient(host="127.0.0.1", port=502, timeout=1.0, unit_id=1, retries=1)
    # connect uses our fake socket
    client.connect()
    regs = client.read_holding_registers(address=0, count=3)
    assert regs == [1, 2, 3]
