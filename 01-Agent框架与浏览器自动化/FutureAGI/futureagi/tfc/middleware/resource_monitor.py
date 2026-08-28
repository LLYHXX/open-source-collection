import time
from concurrent.futures import ThreadPoolExecutor

import psutil
import structlog

logger = structlog.get_logger(__name__)


class ResourceMonitor:
    def __init__(self):
        self.warning_threshold = 85  # Percentage
        self.critical_threshold = 95  # Percentage
        self._monitor_thread = ThreadPoolExecutor(
            max_workers=10, thread_name_prefix="monitor_thread"
        )

    def start_monitoring(self):
        if not self._monitor_thread:
            self._monitor_thread.submit(self._monitor_resources)

    def _monitor_resources(self):
        while True:
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.critical_threshold:
                logger.critical(f"Critical CPU usage: {cpu_percent}%")
            elif cpu_percent > self.warning_threshold:
                logger.warning(f"High CPU usage: {cpu_percent}%")

            # Memory Usage
            memory = psutil.virtual_memory()
            if memory.percent > self.critical_threshold:
                logger.critical(f"Critical memory usage: {memory.percent}%")
            elif memory.percent > self.warning_threshold:
                logger.warning(f"High memory usage: {memory.percent}%")

            # Disk Usage
            disk = psutil.disk_usage("/")
            if disk.percent > self.critical_threshold:
                logger.critical(f"Critical disk usage: {disk.percent}%")
            elif disk.percent > self.warning_threshold:
                logger.warning(f"High disk usage: {disk.percent}%")

            time.sleep(60)  # Check every minute


# Initialize resource monitoring
resource_monitor = ResourceMonitor()
