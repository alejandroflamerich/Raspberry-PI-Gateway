"""Compatibility re-exports to the new `sw.modbus` subpackage."""

from app.modules.sw.modbus import (
    MockModbusClient,
    TcpModbusClient,
    get_modbus_client,
    IModbusTcpClient,
)

__all__ = [
    "MockModbusClient",
    "TcpModbusClient",
    "get_modbus_client",
    "IModbusTcpClient",
]
