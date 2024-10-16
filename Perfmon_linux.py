import os
import psutil
import subprocess
import logging
import time
import signal
import shutil  # For checking if commands are available

"""
Linux Performance Monitoring Script

Version: 1.0
Date: October 2024
Author: [Brian Knight]

DESCRIPTION:
This script collects detailed performance data from a Linux system, including CPU, memory, disk, paging, network, and NFS-related statistics. 
It is designed to monitor key system metrics and log the information to a file for later analysis. The script is suitable for running on 
Linux systems and can collect data over a specified duration.

DATA COLLECTED:
1. **System Information**:
   - Linux kernel and OS information via `uname -a`.
   - Distribution details via `lsb_release -a`.

2. **CPU and Memory Usage**:
   - CPU usage percentage collected via `psutil.cpu_percent()`.
   - Memory usage, total memory, and available memory via `psutil.virtual_memory()`.
   - Additional CPU stats from `/proc/stat`.

3. **Disk Usage and I/O Statistics**:
   - Disk partition usage via `psutil.disk_usage()` for each mount point.
   - Detailed disk I/O stats via `iostat` (if available), otherwise fallback to `vmstat`.

4. **Network Usage**:
   - Bytes sent/received via `psutil.net_io_counters()`.
   - Network interface statistics via `netstat -i`.
   - Socket statistics via `ss -s`.

5. **Process Monitoring**:
   - High CPU and memory-consuming processes identified via `psutil.process_iter()`.
   - Detailed process statistics via the `top` command.
   - Visualization of the process tree via `pstree`.
   - Open file handles via `lsof`.

6. **Paging and Swap Stats**:
   - Swap memory usage via `psutil.swap_memory()`.
   - Additional paging information from `vmstat`.

7. **Filesystem Stats**:
   - Disk usage of mounted filesystems via `df -h`.
   - Mount points and their types via `mount`.
   - Disk usage of specific directories (e.g., `/var`) via `du -sh`.

8. **NFS Monitoring**:
   - NFS client and server statistics via `nfsstat` (if available).
   - List of active NFS mounts from `/proc/mounts`.

9. **Log Monitoring**:
   - Recent system logs from `/var/log/syslog` (or `/var/log/messages` for Red Hat-based systems).

10. **Error Handling**:
    - The script logs warnings if certain commands (e.g., `nfsstat`) are not available.
    - Graceful termination with cleanup if the script is interrupted (e.g., via Ctrl+C).


USAGE:
1. Ensure Python3 is installed on your system.
2. Install the required Python libraries: `psutil`, `shutil`, and `subprocess`.
3. Run the script as root or with sudo privileges to collect full system metrics:

    sudo python3 Perfmon_linux.py

NOTES:
- This script is intended for Linux systems and may require slight modifications for compatibility with other UNIX-based operating systems.
- The script logs the output to `/tmp/Linux_Perf_Monitor_<PID>.log`, where `<PID>` is the process ID of the running script.
"""

# Setup logging
LOGFILE = f"/tmp/Linux_Perf_Monitor_{os.getpid()}.log"
logging.basicConfig(filename=LOGFILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration: Duration in seconds to run the monitoring
RUN_DURATION = 60  # Run for 60 seconds
CHECK_INTERVAL = 10  # Collect stats every 10 seconds
CPU_ALERT_THRESHOLD = 90  # Alert if CPU usage exceeds 90%
MEMORY_ALERT_THRESHOLD = 90  # Alert if memory usage exceeds 90%

# Signal handler for cleanup on exit
def signal_handler(signum, frame):
    logging.info(f"Received signal {signum}, cleaning up...")
    cleanup()
    exit(1)

# Trap signals
for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]:
    signal.signal(sig, signal_handler)

# Cleanup function
def cleanup():
    logging.info("Cleaning up resources before exiting.")

# Run system commands with subprocess
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        logging.info(output)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")

# CPU and memory monitoring with alerting
def cpu_memory_stats():
    logging.info("CPU and Memory Stats:")
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Logging CPU and Memory usage
    logging.info(f"CPU Usage: {cpu_percent}%")
    logging.info(f"Total Memory: {memory.total / (1024 ** 3):.2f} GB")
    logging.info(f"Used Memory: {memory.used / (1024 ** 3):.2f} GB")
    logging.info(f"Available Memory: {memory.available / (1024 ** 3):.2f} GB")

    # CPU and Memory Alerting
    if cpu_percent > CPU_ALERT_THRESHOLD:
        logging.warning(f"ALERT: CPU usage is high at {cpu_percent}%")
    if memory.percent > MEMORY_ALERT_THRESHOLD:
        logging.warning(f"ALERT: Memory usage is high at {memory.percent}%")
    
    # Collecting additional CPU stats from /proc/stat
    run_command("cat /proc/stat | head -n 5")

# Disk usage monitoring with enhanced I/O stats
def disk_stats():
    logging.info("Disk Usage Stats:")
    partitions = psutil.disk_partitions()
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            logging.info(f"Disk {partition.device}:")
            logging.info(f"  Total: {usage.total / (1024 ** 3):.2f} GB")
            logging.info(f"  Used: {usage.used / (1024 ** 3):.2f} GB")
            logging.info(f"  Free: {usage.free / (1024 ** 3):.2f} GB")
            logging.info(f"  Percent Used: {usage.percent}%")
        except PermissionError:
            logging.warning(f"Permission denied for {partition.mountpoint}")

    # Enhanced disk I/O monitoring
    if shutil.which("iostat"):
        run_command("iostat -xm 1 5")
    else:
        run_command("vmstat 1 5")  # Fallback if iostat is missing

# Network usage monitoring with socket statistics
def network_stats():
    logging.info("Network Stats:")
    net_io = psutil.net_io_counters()
    logging.info(f"Bytes Sent: {net_io.bytes_sent / (1024 ** 2):.2f} MB")
    logging.info(f"Bytes Received: {net_io.bytes_recv / (1024 ** 2):.2f} MB")

    # Running additional network commands
    run_command("netstat -i")
    run_command("ss -s")  # Summary of socket stats

# Process monitoring with thread-level and file handle stats
def process_stats():
    logging.info("Process Monitoring:")
    # Long-running processes and CPU utilization
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
        try:
            proc_info = proc.info
            if proc_info['cpu_percent'] > 50:  # Log processes using more than 50% CPU
                logging.warning(f"High CPU Usage: PID: {proc_info['pid']}, Name: {proc_info['name']}, CPU: {proc_info['cpu_percent']}%, Mem: {proc_info['memory_percent']}%")
        except psutil.AccessDenied:
            logging.warning(f"Access denied to process: {proc_info['pid']}")

    # Running top command for detailed process stats
    run_command("top -bn1")

    # Capture open file handles with lsof
    run_command("lsof")

    # Visualize process tree
    run_command("pstree")  # Process hierarchy visualization

# Paging and swap space stats
def paging_stats():
    logging.info("Paging and Swap Stats:")
    swap = psutil.swap_memory()
    logging.info(f"Total Swap: {swap.total / (1024 ** 3):.2f} GB")
    logging.info(f"Used Swap: {swap.used / (1024 ** 3):.2f} GB")
    logging.info(f"Free Swap: {swap.free / (1024 ** 3):.2f} GB")
    logging.info(f"Swap In: {swap.sin / (1024 ** 2):.2f} MB")
    logging.info(f"Swap Out: {swap.sout / (1024 ** 2):.2f} MB")

    # Using vmstat for additional stats
    run_command("vmstat 1 5")

# Filesystem statistics
def filesystem_stats():
    logging.info("Filesystem Stats:")
    run_command("df -h")
    run_command("mount")
    run_command("du -sh /var")  # Checking size of /var as an example

# NFS monitoring
def nfs_stats():
    logging.info("NFS Stats:")
    # Checking NFS client/server statistics using nfsstat
    try:
        if shutil.which("nfsstat"):
            run_command("nfsstat -s")  # Server statistics
            run_command("nfsstat -c")  # Client statistics
        else:
            logging.warning("nfsstat command not found.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get NFS stats: {e}")

# Check active NFS mounts
def check_nfs_mounts():
    logging.info("Checking active NFS mounts:")
    try:
        with open("/proc/mounts", "r") as f:
            nfs_mounts = [line for line in f if "nfs" in line]
            if nfs_mounts:
                logging.info(f"NFS Mounts:\n{''.join(nfs_mounts)}")
            else:
                logging.info("No NFS mounts found.")
    except Exception as e:
        logging.error(f"Error checking NFS mounts: {e}")

# Log monitoring
def log_monitoring():
    logging.info("System Logs:")
    # Fetch recent logs from syslog
    run_command("tail -n 50 /var/log/syslog")  # For Ubuntu-based systems
    run_command("tail -n 50 /var/log/messages")  # For Red Hat-based systems

# General system info (logged once)
def system_info():
    logging.info("System Info:")
    run_command("uname -a")
    run_command("lsb_release -a")  # For Linux distribution details

# Main function to loop for a defined period
def main():
    logging.info("Starting Linux performance monitoring...")

    # Log system info once at the start
    system_info()

    # Run monitoring for the configured duration
    start_time = time.time()
    while (time.time() - start_time) < RUN_DURATION:
        logging.info("Collecting system stats...")

        # Collect system stats
        cpu_memory_stats()
        disk_stats()
        network_stats()
        process_stats()
        paging_stats()
        filesystem_stats()
        nfs_stats()  # Added NFS stats collection
        check_nfs_mounts()  # Check NFS mounts
        log_monitoring()

        logging.info(f"Sleeping for {CHECK_INTERVAL} seconds...")
        time.sleep(CHECK_INTERVAL)

    logging.info("Linux performance monitoring completed after the set duration.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
        logging.info("Monitoring stopped by user.")

