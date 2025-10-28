import yaml
import os
from jinja2 import Environment, FileSystemLoader

# Đường dẫn đến thư mục chứa các file cấu hình
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")

def render_yaml_template(filename, context=None):
    """Render Jinja2 template từ file YAML"""
    path = os.path.join(CONFIG_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    env = Environment(loader=FileSystemLoader(CONFIG_DIR), keep_trailing_newline=True)
    template = env.from_string(content)
    return template.render(**(context or {}))

def load_yaml_file(filename, context=None):
    """Load YAML, tự động render nếu có Jinja2"""
    path = os.path.join(CONFIG_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    has_jinja = "{%" in content or "{{" in content
    if has_jinja:
        rendered = render_yaml_template(filename, context)
        try:
            return yaml.safe_load(rendered)
        except yaml.YAMLError as e:
            print(f"❌ YAML parse error in {filename}: {e}")
            print("🔍 Nội dung sau khi render:")
            print("=" * 60)
            print(rendered)
            print("=" * 60)
            raise
    else:
        return yaml.safe_load(content)

def load_config():
    """Load toàn bộ cấu hình từ các file YAML"""
    config = {}

    # Load project trước để dùng làm context nếu cần
    config["projects"] = load_yaml_file("projects.yaml")
    project = config["projects"]["projects"][0] if config["projects"].get("projects") else {}

    # Load các phần còn lại
    config["inverters"] = load_yaml_file("devices.yaml").get("inverters", [])
    config["mppt_channels"] = load_yaml_file("mppt.yaml", context=project).get("mppt_channels", [])
    config["strings"] = load_yaml_file("strings.yaml", context=project).get("strings", [])
    config["server"] = load_yaml_file("server.yaml").get("server", {})

    return config
