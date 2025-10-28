"""Test toàn bộ cấu hình từ config_loader.py"""
from utils.config_loader import load_config

def main():
    print("🔧 Đang kiểm tra file config_loader.py...\n")

    try:
        config = load_config()
        print("✅ Đã load thành công toàn bộ cấu hình!\n")

        # === PROJECTS ===
        print("=" * 60)
        print("📁 PROJECTS")
        print("=" * 60)
        projects = config.get("projects", {}).get("projects", [])
        print(f"Số lượng project: {len(projects)}")
        if projects:
            p = projects[0]
            print(f"  • {p['name']} tại {p['location']} (ID={p['id']})")

        # === INVERTERS ===
        print("\n" + "=" * 60)
        print("⚡ INVERTERS")
        print("=" * 60)
        inverters = config.get("inverters", [])
        print(f"Số lượng inverter: {len(inverters)}")
        for inv in inverters:
            print(f"  • Inverter {inv['id']}: {inv['brand']} {inv['model']}")

        # === MPPT CHANNELS ===
        print("\n" + "=" * 60)
        print("📊 MPPT CHANNELS")
        print("=" * 60)
        mppts = config.get("mppt_channels", [])
        print(f"Số lượng MPPT: {len(mppts)}")
        for m in mppts:
            print(f"  • MPPT ID={m['id']}, Inverter={m['inverter_id']}, MPPT Index={m['mppt_index']}, Max_P={m['Max_P']}W")

        # === MPPT của 3 inverter SG110CX ===
        print("\n" + "=" * 60)
        print("📊 MPPT của 3 inverter Sungrow SG110CX (ID: 1, 2, 3)")
        print("=" * 60)
        sg110_ids = [1, 2, 3]
        sg110_mppts = [m for m in mppts if m["inverter_id"] in sg110_ids]
        print(f"Tổng cộng: {len(sg110_mppts)} MPPT")
        for m in sg110_mppts:
            print(f"  • MPPT ID={m['id']}, Inverter={m['inverter_id']}, MPPT Index={m['mppt_index']}, Max_P={m['Max_P']}W")

        # === STRINGS ===
        print("\n" + "=" * 60)
        print("🔗 STRINGS")
        print("=" * 60)
        strings = config.get("strings", [])
        print(f"Số lượng strings: {len(strings)}")
        for s in strings:
            print(f"  • String ID={s['id']}, MPPT={s['mppt_id']}, Inverter={s.get('inverter_id', 'N/A')}, Max_P={s.get('Max_P', 'N/A')}W")

        # === SERVER CONFIG ===
        print("\n" + "=" * 60)
        print("🌐 SERVER CONFIG")
        print("=" * 60)
        server = config.get("server", {})
        modbus_tcp = server.get("modbus_tcp", {})
        print(f"Modbus TCP: {'✅ Enabled' if modbus_tcp.get('enabled') else '❌ Disabled'}")
        if modbus_tcp.get("enabled"):
            print(f"  • Port: {modbus_tcp.get('port')}")

        print("\n🎉 Kiểm tra hoàn tất!")
        # === STRINGS của inverter 1 ===
        print("\n" + "=" * 60)
        print("🔗 STRINGS của inverter 1")
        print("=" * 60)
        inverter_1_strings = [s for s in strings if s.get("inverter_id") == 1]
        print(f"Tổng cộng: {len(inverter_1_strings)} strings")
        for s in inverter_1_strings:
            print(f"  • String ID={s['id']}, MPPT={s['mppt_id']},INV={s.get('inverter_id', 'N/A')}, Max_P={s.get('Max_P', 'N/A')}W")
        # === STRINGS của inverter 4 ===
        print("\n" + "=" * 60)
        print("🔗 STRINGS của inverter 4")
        print("=" * 60)
        inverter_4_strings = [s for s in strings if s.get("inverter_id") == 4]
        print(f"Tổng cộng: {len(inverter_4_strings)} strings")
        for s in inverter_4_strings:
            print(f"  • String ID={s['id']}, MPPT={s['mppt_id']},INV={s.get('inverter_id', 'N/A')}, Max_P={s.get('Max_P', 'N/A')}W")
    except Exception as e:
        print(f"\n❌ Lỗi khi load cấu hình: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
