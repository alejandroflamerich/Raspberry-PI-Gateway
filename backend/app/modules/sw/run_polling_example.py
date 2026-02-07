"""Run multiple pollers against a Modbus server (example runner).

Usage:
  cd backend
  python -m app.modules.sw.run_polling_example

Environment variables:
  HW_MODE      - "tcp" (default) or "mock"
  MODBUS_HOST  - host (default 127.0.0.1)
  MODBUS_PORT  - port (default 502)
  MODBUS_UNIT  - unit id (default 1)
  DURATION     - seconds to run (default 10)
"""
"""Run pollers based on a JSON configuration file.

Example usage:
    cd backend
    python -m app.modules.sw.run_polling_example --config polling_config.json

The JSON contains `devices` and `pollers` arrays and an optional `duration` in seconds.
"""
import logging
import os
import time

import argparse
import json
from typing import Dict

from app.modules.sw.modbus import ModbusManager, Poller
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("run_polling_example")


def load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("run_polling_example")


def main():
    hw_mode = os.getenv("HW_MODE", "tcp")
    host = os.getenv("MODBUS_HOST", "127.0.0.1")
    port = int(os.getenv("MODBUS_PORT", "502"))
    unit = int(os.getenv("MODBUS_UNIT", "1"))
    duration = float(os.getenv("DURATION", "10"))

    manager = ModbusManager()

    def cb(name):
        def _cb(res, err):
            if err:
                logger.warning("%s poll error: %s", name, err)
            else:
                logger.info("%s poll result: %s", name, res)
        return _cb

    client = manager.get_client(hw_mode=hw_mode, host=host, port=port, unit_id=unit)

    p1 = Poller(client, "holding", address=0, count=4, interval=1.0, callback=cb("analog-1"), name="analog-1")
    p2 = Poller(client, "input", address=100, count=2, interval=2.0, callback=cb("digital-1"), name="digital-1")

    # start
    for p in (p1, p2):
        p.start()

    logger.info("Running pollers for %s seconds (hw_mode=%s %s:%s)", duration, hw_mode, host, port)
    try:
        end = time.time() + duration
        while time.time() < end:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        for p in (p1, p2):
            p.stop()
            p.join(timeout=1.0)
        manager.close_all()
        logger.info("Stopped")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", default="polling_config.json", help="Path to JSON config (relative to backend)")
    parser.add_argument("--duration", "-t", type=float, default=None, help="Override duration in config (seconds)")
    args = parser.parse_args()

    cfg_path = args.config
    if not os.path.isabs(cfg_path):
        cfg_path = os.path.join(os.getcwd(), cfg_path)

    if not os.path.exists(cfg_path):
        logger.error("Config file not found: %s", cfg_path)
        return

    cfg = load_config(cfg_path)
    # populate easyberry database at program start
    try:
        from app.modules.sw.easyberry import loader as _eb_loader
        from app.modules.sw.easyberry.store import database

        # prefer an explicit easyberry_config.json if present
        eb_path = os.path.join(os.getcwd(), "easyberry_config.json")
        if os.path.exists(eb_path):
            try:
                _eb_loader.load_from_file(eb_path)
                logger.info("Loaded easyberry config from %s", eb_path)
            except Exception:
                logger.exception("Failed loading easyberry_config.json")
        else:
            # Do not merge or load pollers from polling config into the database.
            # The database should be controlled by `easyberry_config.json` only;
            # polling config is used solely to create Poller instances.
            logger.info("No easyberry_config.json found; leaving database unchanged")
    except Exception:
        logger.debug("No easyberry module available to load config")
    # print current easyberry database to console for debugging/inspection
    try:
        from app.modules.sw.easyberry.store import database
        snapshot = {
            "pollers": database.get_pollers(),
            "mbid_index": {k: {"poller_id": v[0], "thing": v[1]} for k, v in getattr(database, "mbid_index", {}).items()},
        }
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.debug("Failed to print easyberry database: %s", e)
    duration = args.duration if args.duration is not None else float(cfg.get("duration", 10.0))

    manager = ModbusManager()


    pollers = []

    def make_cb(name):
        def _cb(res, err):
            if err:
                logger.warning("%s poll error: %s", name, err)
            else:
                logger.info("%s poll result: %s", name, res)

        return _cb

    # Iterate devices and their embedded pollers. Poller entries must NOT
    # include `unit_id`; if they do, the device `unit_id` is used and the
    # poller value is ignored (with a warning logged).
    for dev in cfg.get("devices", []):
        dev_id = dev.get("id") or "<unknown>"
        hw_mode = dev.get("hw_mode", "tcp")
        host = dev.get("host", "127.0.0.1")
        port = int(dev.get("port", 502))
        timeout = float(dev.get("timeout", 3.0))
        retries = int(dev.get("retries", 1))
        unit = int(dev.get("unit_id", 1))

        for pconf in dev.get("pollers", []):
            local_pid = pconf.get("id") or pconf.get("name") or f"poller-{len(pollers)+1}"
            if "unit_id" in pconf:
                logger.warning("Poller %s in device %s contains 'unit_id'; ignoring and using device unit_id=%s", local_pid, dev_id, unit)

            # use device unit as the device identifier; compose poller id including unit
            full_pid = f"{unit}-{local_pid}"

            client = manager.get_client(
                hw_mode=hw_mode,
                host=host,
                port=port,
                timeout=timeout,
                unit_id=unit,
                retries=retries,
            )

            poller = Poller(
                client,
                pconf.get("function", "holding"),
                address=int(pconf.get("address", 0)),
                count=int(pconf.get("count", 1)),
                interval=float(pconf.get("interval", 1.0)),
                callback=make_cb(full_pid),
                unit_id=unit,
                name=full_pid,
                poller_id=full_pid,
            )
            pollers.append(poller)

    for p in pollers:
        p.start()

    logger.info("Running pollers for %s seconds (config=%s)", duration, cfg_path)
    try:
        end = time.time() + duration
        while time.time() < end:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        for p in pollers:
            p.stop()
            p.join(timeout=1.0)
        manager.close_all()
        logger.info("Stopped")


if __name__ == "__main__":
    main()
