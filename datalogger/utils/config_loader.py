import yaml
import os

CONFIG_DIR = "config"

def load_yaml_file(filename):
    path = os.path.join(CONFIG_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_config():
    config = {}

    # Load từng file cấu hình
    config["projects"] = load_yaml_file("projects.yaml")
    config["inverters"] = load_yaml_file("devices.yaml").get("inverters", [])
    config["mppt_channels"] = load_yaml_file("mppt.yaml").get("mppt_channels", [])
    config["strings"] = load_yaml_file("string.yaml").get("strings", [])
    config["server"] = load_yaml_file("server.yaml").get("server", {})

    return config
