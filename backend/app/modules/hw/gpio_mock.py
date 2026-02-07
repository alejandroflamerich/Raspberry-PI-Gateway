from app.modules.hw.interfaces import IGpioDriver


class MockGpioDriver(IGpioDriver):
    def __init__(self):
        self._state = {}

    def read(self, pin: int) -> int:
        return self._state.get(pin, 0)

    def write(self, pin: int, value: int) -> None:
        self._state[pin] = int(value)
