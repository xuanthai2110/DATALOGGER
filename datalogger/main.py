import asyncio
from engine.collector import start_all_polling
from utils.config_loader import load_config

def build_inverter_configs(config):
    return [
        {
            "id": inv["id"],
            "port": "/dev/ttyUSB0",  # hoặc từ cấu hình
            "slave_id": 1,
            "mppt_count": inv.get("mppt_count", 9),
            "string_count": inv.get("string_count", 18)
        }
        for inv in config["inverters"]
    ]

if __name__ == "__main__":
    config = load_config()
    inverter_configs = build_inverter_configs(config)
    asyncio.run(start_all_polling(inverter_configs))
