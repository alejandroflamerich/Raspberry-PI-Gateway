try:
    import RPi.GPIO as GPIO
except Exception:
    GPIO = None

from app.modules.hw.interfaces import IGpioDriver


class PiGpioDriver(IGpioDriver):
    def __init__(self):
        if GPIO is None:
            raise RuntimeError("RPi.GPIO not available on this platform")
        GPIO.setmode(GPIO.BCM)

    def read(self, pin: int) -> int:
        return GPIO.input(pin)

    def write(self, pin: int, value: int) -> None:
        GPIO.output(pin, value)
