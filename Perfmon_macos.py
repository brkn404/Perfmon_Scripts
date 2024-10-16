import os
import subprocess
import logging
import time
import signal

"""
MacOS Performance Monitoring Script

Version: 1.0
Date: October 2024
Author: Brian Knight

This script collects various system performance data on macOS, including:
- System information
- CPU, memory, disk, and I/O statistics
- Process and network monitoring
- Filesystem and NFS stats
- Error log monitoring

### Commands used:

1. **System Information:**
   - `uname -a`: Provides system kernel information.
   - `sw_vers`: Displays macOS version details.
   
2. **CPU and Memory Stats:**
   - `vm_stat`: Shows virtual memory statistics.
   - `sysctl -a | grep machdep.cpu`: CPU-related stats.
   - `sysctl -n hw.memsize`: Displays total physical memory.
   - `top -l 1`: Displays real-time system information including CPU and memory usage.

3. **Disk and I/O Stats:**
   - `df -h`: Shows disk usage of mounted filesystems.
   - `diskutil list`: Displays a list of all disks and partitions.
   - `iostat -Id 1 2`: Shows I/O statistics for disk devices.

4. **Process Monitoring:**
   - `ps aux`: Lists running processes.
   - `top -l 1 -n 10`: Lists the top 10 processes by CPU usage.

5. **Network Stats:**
   - `netstat -i`: Network interface statistics.
   - `ifconfig`: Shows network interface configuration.

6. **Filesystem and NFS Stats:**
   - `mount`: Lists mounted filesystems.
   - `nfsstat`: Displays NFS statistics (if configured).

7. **Error Log Monitoring:**
   - `log show --predicate 'eventMessage contains "error"' --info`: Retrieves error logs.
   
Logs are written to `/tmp/MacOS_Perf_Monitor_<pid>.log` for analysis.
"""

# Global constants for monitoring
RUN_DURATION = 60  # Total run time for the script in seconds
CHECK_INTERVAL = 10  # Interval between checks

# Function to run a command and log output
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{command}' failed: {e.stderr.decode('utf-8')}")
        return None

# Logging setup
def setup_logging():
    logging.basicConfig(filename=f'/tmp/MacOS_Perf_Monitor_{os.getpid()}.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Collect system info
def system_info():
    logging.info("Collecting system information...")
    logging.info(run_command("uname -a"))
    logging.info(run_command("sw_vers"))

# Collect CPU and memory stats
def cpu_memory_stats():
    logging.info("Collecting CPU and memory stats...")
    logging.info(run_command("vm_stat"))
    logging.info(run_command("sysctl -a | grep machdep.cpu"))
    logging.info(run_command("sysctl -n hw.memsize"))
    logging.info(run_command("top -l 1"))

# Collect disk and I/O stats
def disk_stats():
    logging.info("Collecting disk and I/O stats...")
    logging.info(run_command("df -h"))
    logging.info(run_command("diskutil list"))
    logging.info(run_command("iostat -Id 1 2"))

# Collect process stats
def process_stats():
    logging.info("Collecting process stats...")
    logging.info(run_command("ps aux"))
    logging.info(run_command("top -l 1 -n 10"))

# Collect network stats
def network_stats():
    logging.info("Collecting network stats...")
    logging.info(run_command("netstat -i"))
    logging.info(run_command("ifconfig"))

# Collect filesystem and NFS stats
def filesystem_nfs_stats():
    logging.info("Collecting filesystem and NFS stats...")
    logging.info(run_command("mount"))
    logging.info(run_command("nfsstat"))

# Collect error logs
def error_logs():
    logging.info("Collecting error logs...")
    logging.info(run_command("log show --predicate 'eventMessage contains \"error\"' --info"))

# Main function to execute monitoring
def main():
    setup_logging()
    start_time = time.time()

    while (time.time() - start_time) < RUN_DURATION:
        system_info()
        cpu_memory_stats()
        disk_stats()
        process_stats()
        network_stats()
        filesystem_nfs_stats()
        error_logs()

        logging.info(f"Sleeping for {CHECK_INTERVAL} seconds...")
        time.sleep(CHECK_INTERVAL)

    logging.info("macOS performance monitoring completed after the set duration.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user.")
