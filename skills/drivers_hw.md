Skill: Hardware Drivers Abstraction

Cuando usar
- Interacción con GPIO, serial, I2C, Modbus; cualquier código que toque hardware.

Objetivo
- Aislar acceso físico detrás de interfaces y permitir implementaciones `mock` y `raspberry`.

Buenas prácticas
- Definir protocolos/interfaces (Python `Protocol` o ABC).
- Proveer `Mock` para desarrollo en PC y `Pi`/`native` impl para Raspberry.
- No importar librerías hardware en módulos globales (usar try/except o fábricas).

Patrón recomendado
- `IGpioDriver` con `read(pin)`, `write(pin, value)`.
- Fábrica `get_gpio_driver()` que devuelve `MockGpioDriver` o `PiGpioDriver` según `settings.hw_mode`.

Checklist
- [ ] Interfaces en `modules/hw/interfaces.py`
- [ ] Implementación mock y stub Pi
