Skill: Protocols — Modbus / DNP3 (edge protocols)

Cuando usar
- Implementar comunicación con PLCs o equipos industriales en el edge.

Buenas prácticas
- Empezar con cliente stub/mock para permitir desarrollo en PC.
- Mantener la lógica de protocolo en módulos separados con adaptadores.
- Para Modbus usar `pymodbus` en Pi; para DNP3 investigar `opendnp3` bindings.

Patrón
- `IModbusTcpClient` con métodos `read_holding_registers(address, count)` y `write_register(address, value)`.
- Implementación `MockModbusClient` y `PymodbusClient` (real) en Raspberry.

Checklist
- [ ] Stub que devuelva datos coherentes para UI/tests
- [ ] Documentar requisitos de librerías nativas para Pi
