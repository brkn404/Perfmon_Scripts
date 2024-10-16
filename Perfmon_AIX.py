import os
import subprocess
import logging
import time
import signal
import threading

"""
AIX Performance Monitoring Script

Version: 1.0
Date: October 2024
Author: Brian Knight

This script collects various system performance data on AIX systems, including:
- System information
- CPU, memory, disk, and I/O statistics
- Volume group and logical volume details
- Network statistics
- Process and paging space monitoring
- Filesystem and NFS stats
- Error log monitoring

The script runs in intervals defined by `RUN_DURATION` and `CHECK_INTERVAL`. It can be configured to run for a specified duration and collect data at set intervals. 

### Notes on the commands used:

1. **System Information:**
   - `uname -a`: Provides detailed system information (kernel name, hostname, OS version, etc.).
   - `oslevel -s`: Displays the AIX operating system version and service pack level.
   - `lsattr -El sys0`: Lists important system attributes such as maximum number of processes, memory settings, etc.
   - `pmcycles -d`: Shows processor cycles and details about the CPU's performance.
   - `lparstat -i`: Lists LPAR (Logical Partition) information, which is important in virtualized environments.

2. **CPU and Memory Stats:**
   - `vmstat 1 3`: Collects virtual memory statistics (CPU utilization, memory usage) with three 1-second samples.
   - `lsattr -El sys0`: Lists system attributes, including CPU and memory settings.
   - `mpstat 1 3`: Provides CPU usage statistics for multiple processors with three 1-second samples.
   - `svmon -G -O affinity=on`: Displays memory affinity details, which shows how memory is distributed across affinity domains.

3. **Disk and I/O Stats:**
   - `lspv`: Lists all physical volumes (disks) attached to the system.
   - `lsattr -El <disk>`: Shows detailed attributes for each disk, such as block size and queue depth.
   - `iostat -DlR <disk> 1 1`: Provides detailed disk I/O statistics for each physical volume.

4. **Volume Group and Logical Volume Stats:**
   - `lsvg`: Lists all volume groups on the system.
   - `lsvg <vg>`: Displays detailed information about each volume group, including free space, total size, etc.
   - `lsvg -l <vg>`: Lists all logical volumes within the specified volume group.
   - `lslv -l <lv>`: Displays detailed information about the logical volumes, including the physical disks they span across.
   - `lslv -m <lv>`: Shows the mapping of logical volumes to physical volumes.

5. **Network Stats:**
   - `netstat -v`: Provides detailed network interface statistics.
   - `entstat -d ent0`: Collects statistics for the ent0 Ethernet adapter.
   - `ifconfig -a`: Lists all network interfaces and their configurations (IP addresses, netmasks, etc.).

6. **Process Monitoring:**
   - `ps -ef`: Displays a detailed list of all running processes on the system.
   - `svmon -G`: Provides global memory usage statistics, including paging and real memory.
   - `svmon -P`: Shows memory usage per process.
   - `topas`: Real-time system monitor for processes, CPU, and memory usage.

7. **Paging and Swap Stats:**
   - `lsps -a`: Lists paging space details, including size and percentage used.
   - `vmstat -s`: Provides detailed memory statistics, including free pages, page faults, etc.

8. **Filesystem and NFS Stats:**
   - `lsfs`: Lists all mounted filesystems and their properties.
   - `nfsstat -s`: Displays NFS server statistics.
   - `nfsstat -c`: Displays NFS client statistics.
   - `mount`: Lists all mounted filesystems.

9. **Error Log Monitoring:**
   - `errpt -a`: Displays the AIX error report, showing system errors and warnings.
   
The script collects this information and logs it into `/tmp/AIX_Perf_Monitor_<pid>.log` for analysis.

### Configuration:
- `RUN_DURATION`: Total time in seconds to run the script.
- `CHECK_INTERVAL`: Time in seconds between each data collection cycle.

"""


# Setup logging
LOGFILE = f"/tmp/AIX_Perf_Monitor_{os.getpid()}.log"
logging.basicConfig(filename=LOGFILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration: Duration in seconds to run the monitoring
RUN_DURATION = 30  # Set as per testing
CHECK_INTERVAL = 5  # Interval between data collection

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

# Run system commands with subprocess and add timeout
def run_command(command, timeout=60):
    """
    Executes a system command with an optional timeout.
    """
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        output = result.stdout.decode('utf-8')
        logging.info(output)
    except subprocess.TimeoutExpired:
        logging.warning(f"Command '{command}' timed out after {timeout} seconds.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{command}' failed: {e}")

# System Information
def system_info():
    """
    Collects basic system information using:
    - `uname -a`: Displays system name and kernel details.
    - `oslevel -s`: Shows the AIX version and technology level.
    - `lsattr -El sys0`: Lists system-level attributes.
    - `pmcycles -d`: Displays processor cycles per second.
    - `lparstat -i`: Provides detailed LPAR (Logical Partition) information.
    """
    logging.info("System Information:")
    run_command("uname -a")
    run_command("oslevel -s")
    run_command("lsattr -El sys0")
    run_command("pmcycles -d")  # Processor cycles
    run_command("lparstat -i")  # LPAR details

# CPU and Memory Stats
def cpu_memory_stats():
    """
    Collects CPU and memory statistics:
    - `vmstat 1 3`: Monitors virtual memory statistics.
    - `lsattr -El sys0`: Lists system attributes like maxuproc, minfree, maxfree.
    - `mpstat 1 3`: Provides CPU usage per processor.
    - `svmon -G`: Displays memory usage, including affinity domains and memory sizes.
    """
    logging.info("CPU and Memory Stats:")
    run_command("vmstat 1 3")  # Reduced to 3 samples
    run_command("lsattr -El sys0")
    run_command("mpstat 1 3")
    run_command("svmon -G -O affinity=on | head -n 20")  # Limiting svmon output

# Disk and I/O Stats
def disk_stats():
    """
    Collects disk and I/O statistics:
    - `lspv`: Lists all physical volumes (disks).
    - `lsattr -El <disk>`: Retrieves disk attributes.
    - `iostat -DlR <disk>`: Monitors disk I/O statistics for each disk.
    """
    logging.info("Collecting Disk Stats:")
    
    # List all physical volumes (disks)
    run_command("lspv")
    
    # Collect disk attributes for each attached disk
    result = subprocess.run("lspv", shell=True, stdout=subprocess.PIPE)
    disks = result.stdout.decode('utf-8').splitlines()
    
    for disk in disks:
        disk_name = disk.split()[0]
        logging.info(f"Collecting information for disk: {disk_name}")
        run_command(f"lsattr -El {disk_name}")  # Disk attributes
        run_command(f"iostat -DlR {disk_name} 1 1", timeout=30)  # Reduced iteration count for testing

# Volume Group Stats
def volume_group_stats():
    """
    Collects volume group statistics:
    - `lsvg`: Lists all volume groups.
    - `lsvg <vg>`: Retrieves volume group details.
    - `lsvg -l <vg>`: Lists logical volumes in the volume group.
    - `lsvg -p <vg>`: Lists physical volumes in the volume group.
    - `lslv -l <lv>`: Retrieves logical volume details.
    - `lslv -m <lv>`: Retrieves logical volume map (physical locations).
    """
    logging.info("Collecting Volume Group Stats:")
    
    # List all volume groups
    result = subprocess.run("lsvg", shell=True, stdout=subprocess.PIPE)
    vgs = result.stdout.decode('utf-8').splitlines()
    
    for vg in vgs:
        logging.info(f"Collecting information for volume group: {vg}")
        run_command(f"lsvg {vg}")      # Volume group attributes
        run_command(f"lsvg -l {vg}")   # List logical volumes in this group
        run_command(f"lsvg -p {vg}")   # List physical volumes in this group
        
        # Collect details for all logical volumes
        result_lv = subprocess.run(f"lsvg -l {vg}", shell=True, stdout=subprocess.PIPE)
        lvs = result_lv.stdout.decode('utf-8').splitlines()
        
        for lv in lvs[1:]:  # Collect info for all logical volumes
            lv_name = lv.split()[0]
            logging.info(f"Collecting information for logical volume: {lv_name}")
            run_command(f"lslv -l {lv_name}")  # Logical volume details
            run_command(f"lslv -m {lv_name}")  # Logical volume map

# Network Stats
def network_stats():
    """
    Collects network statistics:
    - `netstat -v`: Provides detailed network statistics.
    - `entstat -d ent0`: Shows statistics for an Ethernet interface.
    - `ifconfig -a`: Displays active network interfaces and their configurations.
    """
    logging.info("Network Stats:")
    run_command("netstat -v")
    run_command("entstat -d ent0")
    run_command("ifconfig -a")  # Interface details

# Process Monitoring
def process_stats():
    """
    Collects process-related information:
    - `ps -ef`: Displays all running processes.
    - `svmon -G`: Shows memory usage of the system.
    - `svmon -P`: Displays memory usage by process.
    - `topas`: Provides real-time performance monitoring.
    """
    logging.info("Process Monitoring:")
    run_command("ps -ef")
    run_command("svmon -G")
    run_command("svmon -P | head -n 20")  # Limiting svmon output for processes
    run_command("topas")

# Paging and Swap Stats
def paging_stats():
    """
    Collects paging and swap usage statistics:
    - `lsps -a`: Lists paging space usage.
    - `vmstat -s`: Provides statistics on system memory and paging.
    """
    logging.info("Paging and Swap Stats:")
    run_command("lsps -a")
    run_command("vmstat -s")

# Filesystem and NFS Stats
def filesystem_nfs_stats():
    """
    Collects filesystem and NFS statistics:
    - `lsfs`: Lists all mounted filesystems and their attributes.
    - `nfsstat -s`: Shows NFS server statistics.
    - `nfsstat -c`: Shows NFS client statistics.
    - `mount`: Displays currently mounted filesystems.
    """
    logging.info("Filesystem and NFS Stats:")
    run_command("lsfs")
    run_command("nfsstat -s")
    run_command("nfsstat -c")
    run_command("mount")

# Error Logs
def log_monitoring():
    """
    Monitors system logs:
    - `errpt -a`: Shows detailed error report logs.
    """
    logging.info("System Logs:")
    run_command("errpt -a | head -n 20")  # Reduced log capture for testing

# Parallel execution of disk and network stats
def parallel_tasks():
    threads = []

    # Create separate threads for disk and network stats
    disk_thread = threading.Thread(target=disk_stats)
    network_thread = threading.Thread(target=network_stats)
    
    threads.append(disk_thread)
    threads.append(network_thread)
    
    # Start both threads
    for thread in threads:
        thread.start()
    
    # Wait for both threads to finish
    for thread in threads:
        thread.join()

# Main function to loop for a defined period
def main():
    logging.info("Starting AIX performance monitoring...")

    # Log system info once at the start
    system_info()

    # Run monitoring for the configured duration
    start_time = time.time()
    while (time.time() - start_time) < RUN_DURATION:
        logging.info("Collecting system stats...")

        # Run parallel tasks for quicker execution
        parallel_tasks()

        # Continue other sequential tasks
        cpu_memory_stats()
        volume_group_stats()  # Full volume group and logical volume collection
        process_stats()
        paging_stats()
        filesystem_nfs_stats()
        log_monitoring()

        logging.info(f"Sleeping for {CHECK_INTERVAL} seconds...")
        time.sleep(CHECK_INTERVAL)

    logging.info("AIX performance monitoring completed after the set duration.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
        logging.info("Monitoring stopped by user.")
