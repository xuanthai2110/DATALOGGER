import asyncio
from typing import Dict, Any, Optional
from drivers.sungrow import SungrowDriver
from engine.scheduler import get_scheduler, PollingType, PollingTask

# Storage callback - sẽ được gán từ bên ngoài (cache, DB, TCP server)
storage_callback: Optional[callable] = None

def set_storage_callback(callback: callable):
    """Đăng ký callback để lưu dữ liệu"""
    global storage_callback
    storage_callback = None # Reset callback trước khi đăng ký mới                                                                      
    storage_callback = callback

async def handle_data(inverter_id: int, data_type: str, data: Dict[str, Any]):
    """Xử lý dữ liệu từ inverter"""
    # In ra console
    print(f"[{inverter_id}] {data_type}: {data}")
    
    # Gọi storage callback nếu có
    if storage_callback:
        try:
            await storage_callback(inverter_id, data_type, data)
        except Exception as e:
            print(f"[Collector] ❌ Lỗi lưu dữ liệu: {e}")

async def poll_realtime(driver: SungrowDriver, inverter_id: int):
    """Polling dữ liệu realtime từ driver"""
    data = driver.read_all_realtime()
    if data:
        await handle_data(inverter_id, "ac", data.get("ac", {}))
        await handle_data(inverter_id, "mppt", data.get("mppt", []))
        await handle_data(inverter_id, "strings", data.get("strings", []))
        await handle_data(inverter_id, "error", data.get("error", {}))
        await handle_data(inverter_id, "energy", data.get("energy", {}))
    else:
        raise Exception("Không đọc được dữ liệu realtime")

async def poll_energy(driver: SungrowDriver, inverter_id: int):
    """Polling dữ liệu sản lượng từ driver"""
    energy = driver.read_energy()
    if energy:
        await handle_data(inverter_id, "energy", energy)
    else:
        raise Exception("Không đọc được dữ liệu sản lượng")

async def start_inverter_polling(config: dict, realtime_interval: int = 5, energy_interval: int = 900):
    """Khởi động polling cho một inverter với scheduler"""
    inverter_id = config["id"]
    port = config["port"]
    slave_id = config["slave_id"]
    mppt_count = config.get("mppt_count", 9)
    string_count = config.get("string_count", 18)

    # Tạo driver
    driver = SungrowDriver(port, slave_id, mppt_count, string_count)

    # Lấy scheduler
    scheduler = get_scheduler()
    
    # Tạo handler functions
    async def realtime_handler():
        return await poll_realtime(driver, inverter_id)
    
    async def energy_handler():
        return await poll_energy(driver, inverter_id)
    
    # Đăng ký tasks với scheduler
    scheduler.add_task(inverter_id, PollingTask(
        type=PollingType.REALTIME,
        interval=realtime_interval,
        inverter_id=inverter_id,
        handler=realtime_handler,
        max_retries=3
    ))
    
    scheduler.add_task(inverter_id, PollingTask(
        type=PollingType.ENERGY,
        interval=energy_interval,
        inverter_id=inverter_id,
        handler=energy_handler,
        max_retries=2
    ))
    
    print(f"[Collector] ✅ Đã đăng ký polling cho inverter {inverter_id}")

async def start_all_polling(inverter_configs: list, realtime_interval: int = 5, energy_interval: int = 900):
    """Khởi động polling cho tất cả inverters"""
    scheduler = get_scheduler()
    
    # Đăng ký tất cả inverters
    for config in inverter_configs:
        await start_inverter_polling(config, realtime_interval, energy_interval)
    
    # Khởi động scheduler
    print("[Collector] 🚀 Starting scheduler for all inverters...")
    await scheduler.start_all_tasks()
