import asyncio
from engine.collector import start_all_polling
from utils.config_loader import load_config
import sys
def build_inverter_configs(config):
    return [
        {
            "id": inv["id"],
            "port": inv.get("port", "COM3"),
            "slave_id": inv.get("slave_id", 1),
            "mppt_count": inv.get("mppt_count", 9),
            "string_count": inv.get("string_count", 18)
        }
        for inv in config.get("inverters", [])
    ]

if __name__ == "__main__":
    config = load_config()
    inverter_configs = build_inverter_configs(config)
    asyncio.run(start_all_polling(inverter_configs))
