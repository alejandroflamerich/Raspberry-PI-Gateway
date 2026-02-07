from .interfaces import IModbusTcpClient

import socket
import struct
import threading
from typing import List, Sequence, Optional


class ModbusException(Exception):
    def __init__(self, function_code: int, exception_code: int, message: Optional[str] = None):
        self.function_code = function_code
        self.exception_code = exception_code
        super().__init__(message or f"Modbus exception {hex(function_code)}:{exception_code}")


class MockModbusClient(IModbusTcpClient):
    def read_holding_registers(self, address: int, count: int, unit_id: Optional[int] = None):
        # return simulated register values (zeros)
        return [0 for _ in range(count)]

    def read_input_registers(self, address: int, count: int, unit_id: Optional[int] = None):
        # simulate input registers as zeros
        return [0 for _ in range(count)]


class TcpModbusClient(IModbusTcpClient):
    def __init__(self, host: str = "localhost", port: int = 502, timeout: float = 3.0, unit_id: int = 1, retries: int = 1):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.unit_id = unit_id
        self.retries = retries
        self._sock: Optional[socket.socket] = None
        # use RLock so _next_transaction_id can be called while holding the lock
        self._lock = threading.RLock()
        self._transaction_id = 0
        # last raw request/response bytes (may be None)
        self._last_request: Optional[bytes] = None
        self._last_response: Optional[bytes] = None

    def connect(self, host: Optional[str] = None, port: Optional[int] = None, timeout: Optional[float] = None) -> None:
        if host:
            self.host = host
        if port:
            self.port = port
        if timeout:
            self.timeout = timeout

        self.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect((self.host, self.port))
        except Exception as e:
            s.close()
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")
        self._sock = s

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        self._sock = None

    def is_connected(self) -> bool:
        return self._sock is not None

    def _next_transaction_id(self) -> int:
        with self._lock:
            self._transaction_id = (self._transaction_id + 1) & 0xFFFF
            return self._transaction_id

    def _build_mbap_header(self, transaction_id: int, length: int, unit_id: int) -> bytes:
        # MBAP: Transaction ID (2), Protocol ID (2=0), Length (2), Unit ID (1)
        return struct.pack(
            ">HHHB", transaction_id, 0x0000, length, unit_id
        )

    def _send_request(self, pdu: bytes, unit_id: Optional[int] = None) -> bytes:
        if unit_id is None:
            unit_id = self.unit_id

        if not self._sock:
            self.connect()

        # ensure only one thread uses the socket at a time for send/recv
        last_exc = None
        for attempt in range(max(1, self.retries)):
            try:
                with self._lock:
                    tid = self._next_transaction_id()
                    mbap = self._build_mbap_header(tid, len(pdu) + 1, unit_id)
                    packet = mbap + pdu
                    # store raw request
                    try:
                        self._last_request = packet
                    except Exception:
                        self._last_request = None

                    self._sock.sendall(packet)
                    # read MBAP header first (7 bytes)
                    hdr = self._recv_all(7)
                    if not hdr or len(hdr) < 7:
                        raise ConnectionError("Incomplete MBAP header")
                    recv_tid, proto_id, length = struct.unpack(
                        ">HHH", hdr[:6]
                    )
                    unit = hdr[6]
                    # length includes unit id + pdu
                    remaining = length - 1
                    body = self._recv_all(remaining) if remaining > 0 else b""
                    resp = hdr + body
                    # verify transaction id
                    if recv_tid != tid:
                        raise ConnectionError("Transaction id mismatch")
                    # store raw response
                    try:
                        self._last_response = resp
                    except Exception:
                        self._last_response = None
                    return resp
            except Exception as e:
                last_exc = e
                # attempt reconnect once
                try:
                    self.close()
                    self.connect()
                except Exception:
                    pass
        raise last_exc or ConnectionError("Failed to send modbus request")

    def _recv_all(self, count: int) -> bytes:
        buf = b""
        while len(buf) < count:
            chunk = self._sock.recv(count - len(buf))
            if not chunk:
                break
            buf += chunk
        return buf

    def _parse_response(self, response: bytes, expected_function: int) -> bytes: 
        # response contains MBAP (7) + PDU
        if len(response) < 8:
            raise ConnectionError("Short response")
        pdu = response[7:]
        function = pdu[0]
        if function & 0x80:
            # exception
            exc_code = pdu[1]
            raise ModbusException(function, exc_code)
        if function != expected_function:
            raise ConnectionError(f"Unexpected function code: {function}")
        return pdu[1:]

    def read_holding_registers(self, address: int, count: int, unit_id: Optional[int] = None) -> List[int]:
        # FC=3
        if count < 1 or count > 125:
            raise ValueError("count must be 1..125")
        pdu = struct.pack(
            ">BHH", 3, address & 0xFFFF, count & 0xFFFF
        )
        resp = self._send_request(pdu, unit_id=unit_id)
        data = self._parse_response(resp, expected_function=3)
        if not data:
            return []
        byte_count = data[0]
        registers = []
        for i in range(0, byte_count, 2):
            reg = struct.unpack(">H", data[1 + i:1 + i + 2])[0]
            registers.append(reg)
        return registers

    def read_input_registers(self, address: int, count: int, unit_id: Optional[int] = None) -> List[int]:
        # FC=4
        if count < 1 or count > 125:
            raise ValueError("count must be 1..125")
        pdu = struct.pack(
            ">BHH", 4, address & 0xFFFF, count & 0xFFFF
        )
        resp = self._send_request(pdu, unit_id=unit_id)
        data = self._parse_response(resp, expected_function=4)
        if not data:
            return []
        byte_count = data[0]
        registers = []
        for i in range(0, byte_count, 2):
            reg = struct.unpack(">H", data[1 + i:1 + i + 2])[0]
            registers.append(reg)
        return registers

    def write_single_register(self, address: int, value: int, unit_id: Optional[int] = None) -> bool:
        # FC=6
        pdu = struct.pack(">BHH", 6, address & 0xFFFF, value & 0xFFFF)
        resp = self._send_request(pdu, unit_id=unit_id)
        _ = self._parse_response(resp, expected_function=6)
        return True

    def write_multiple_registers(self, address: int, values: Sequence[int], unit_id: Optional[int] = None) -> bool:
        # FC=16
        count = len(values)
        if count < 1 or count > 123:
            raise ValueError("count must be 1..123")
        byte_count = count * 2
        header = struct.pack(">BHHB", 16, address & 0xFFFF, count & 0xFFFF, byte_count)
        payload = b"".join(struct.pack(">H", v & 0xFFFF) for v in values)
        pdu = header + payload
        resp = self._send_request(pdu, unit_id=unit_id)
        _ = self._parse_response(resp, expected_function=16)
        return True


def get_modbus_client(hw_mode: str = "mock", **cfg) -> IModbusTcpClient:
    """Factory: returns MockModbusClient or TcpModbusClient based on `hw_mode`."""
    if hw_mode == "mock":
        return MockModbusClient()
    return TcpModbusClient(**cfg)
