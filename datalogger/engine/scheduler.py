"""
Scheduler - Quản lý polling schedules cho datalogger
- Hỗ trợ multiple polling intervals
- Retry logic với exponential backoff
- Dynamic schedule updates
"""
import asyncio
import time
from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PollingType(Enum):
    """Loại polling data"""
    REALTIME = "realtime"  # Dữ liệu realtime (AC, MPPT, Strings, Error)
    ENERGY = "energy"      # Sản lượng điện (daily, monthly, total)
    SLOW = "slow"          # Dữ liệu chậm (config, status)


@dataclass
class PollingTask:
    """Thông tin một polling task"""
    type: PollingType
    interval: int          # Interval in seconds
    inverter_id: int
    handler: Callable     # Function to poll data
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0
    last_success: Optional[float] = None
    consecutive_failures: int = 0


class Scheduler:
    """Quản lý polling schedules cho các inverters"""
    
    def __init__(self):
        self.tasks: Dict[int, Dict[PollingType, PollingTask]] = {}
        self.running = False
        
    def add_task(self, inverter_id: int, task: PollingTask):
        """Thêm một polling task"""
        if inverter_id not in self.tasks:
            self.tasks[inverter_id] = {}
        self.tasks[inverter_id][task.type] = task
        
    def get_task(self, inverter_id: int, task_type: PollingType) -> Optional[PollingTask]:
        """Lấy task theo inverter_id và type"""
        if inverter_id not in self.tasks:
            return None
        return self.tasks[inverter_id].get(task_type)
        
    def remove_task(self, inverter_id: int, task_type: Optional[PollingType] = None):
        """Xóa task"""
        if inverter_id not in self.tasks:
            return
            
        if task_type is None:
            # Xóa tất cả tasks của inverter
            del self.tasks[inverter_id]
        else:
            # Xóa task cụ thể
            if task_type in self.tasks[inverter_id]:
                del self.tasks[inverter_id][task_type]
    
    async def run_task(self, task: PollingTask):
        """Chạy một polling task với retry logic"""
        last_error = None
        retry_delay = task.retry_delay
        
        while True:
            try:
                # Gọi handler để lấy dữ liệu
                await task.handler()
                
                # Success
                task.last_success = time.time()
                task.consecutive_failures = 0
                task.retry_count = 0
                retry_delay = task.retry_delay  # Reset retry delay
                
                # Chờ interval trước khi poll lần tiếp
                await asyncio.sleep(task.interval)
                
            except Exception as e:
                last_error = e
                task.consecutive_failures += 1
                
                print(f"[Scheduler] ❌ {task.type.value} for inverter {task.inverter_id} failed: {e}")
                
                # Kiểm tra max retries
                if task.retry_count >= task.max_retries:
                    print(f"[Scheduler] ⚠️ Max retries reached for {task.type.value} (inverter {task.inverter_id})")
                    # Vẫn tiếp tục chạy nhưng chờ lâu hơn
                    task.retry_count = 0
                    await asyncio.sleep(task.interval * 2)  # Chờ gấp đôi
                else:
                    # Exponential backoff
                    task.retry_count += 1
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)  # Max 60 seconds
    
    async def start_inverter_tasks(self, inverter_id: int):
        """Khởi động tất cả tasks cho một inverter"""
        if inverter_id not in self.tasks:
            return
            
        tasks_to_run = []
        for task in self.tasks[inverter_id].values():
            tasks_to_run.append(asyncio.create_task(self.run_task(task)))
        
        # Chờ tất cả tasks (sẽ chạy mãi mãi)
        await asyncio.gather(*tasks_to_run)
    
    async def start_all_tasks(self):
        """Khởi động scheduler cho tất cả inverters"""
        self.running = True
        print("[Scheduler] 🚀 Starting all polling tasks...")
        
        all_tasks = []
        for inverter_id in self.tasks:
            all_tasks.append(asyncio.create_task(self.start_inverter_tasks(inverter_id)))
        
        await asyncio.gather(*all_tasks)
    
    def stop(self):
        """Dừng scheduler"""
        self.running = False
        print("[Scheduler] ⏹️ Stopping scheduler...")
    
    def get_stats(self) -> Dict:
        """Lấy thống kê về scheduler"""
        stats = {}
        for inverter_id, tasks in self.tasks.items():
            inv_stats = {}
            for task_type, task in tasks.items():
                inv_stats[task_type.value] = {
                    "interval": task.interval,
                    "retry_count": task.retry_count,
                    "consecutive_failures": task.consecutive_failures,
                    "last_success": task.last_success,
                    "status": "healthy" if task.consecutive_failures < 3 else "degraded"
                }
            stats[inverter_id] = inv_stats
        return stats
    
    def update_interval(self, inverter_id: int, task_type: PollingType, new_interval: int):
        """Cập nhật interval động"""
        task = self.get_task(inverter_id, task_type)
        if task:
            old_interval = task.interval
            task.interval = new_interval
            print(f"[Scheduler] Updated {task_type.value} interval for inverter {inverter_id}: {old_interval}s → {new_interval}s")
            return True
        return False


# Singleton instance
_scheduler_instance: Optional[Scheduler] = None

def get_scheduler() -> Scheduler:
    """Lấy singleton scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = Scheduler()
    return _scheduler_instance

