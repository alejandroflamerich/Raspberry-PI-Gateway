from typing import Protocol


class IGpioDriver(Protocol):
    def read(self, pin: int) -> int: ...
    def write(self, pin: int, value: int) -> None: ...


