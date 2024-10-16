# Perfmon_Scripts
Performance Monitoring Scripts for Linux, AIX, and macOS
Overview

This repository contains three performance monitoring scripts designed to collect key system metrics on Linux, AIX, and macOS operating systems. The scripts collect data on CPU, memory, disk I/O, network, processes, and filesystem activity, logging the results to a file for analysis.

Each script is tailored to the specific commands available on the operating system it runs on, but all follow a similar pattern for collecting system performance metrics.
Scripts
1. Perfmon_linux.py
2. Perfmon_aix.py
3. Perfmon_macos.py
Installation

These scripts are written in Python 3. Ensure that Python 3 and the necessary system tools (such as iostat, ps, df, etc.) are installed on your machine.
Prerequisites:

    Python 3
    Elevated privileges (some commands may require root or sudo access)

Running the Scripts

Each script can be run directly from the command line. Example for Linux:

sudo python3 Perfmon_linux.py

Logs are saved to /tmp/ with the file name format Perf_Monitor_<pid>.log, where <pid> is the process ID of the script.
Script Behavior

Each script collects data at a configurable interval (CHECK_INTERVAL) and runs for a defined duration (RUN_DURATION), which are set at the beginning of each script. You can adjust these values as needed.
Script Details
Perfmon_linux.py

Description:
This script collects performance metrics on Linux systems, including system info, CPU, memory, disk, network, and process statistics.

Key Commands:

    uname -a: Kernel version and system information.
    lscpu: CPU architecture and details.
    free -m: Memory usage.
    vmstat 1 3: Virtual memory statistics.
    iostat -x 1 3: Disk I/O statistics.
    df -h: Disk space usage.
    netstat -i: Network interface statistics.
    ps aux: Process monitoring.
    nfsstat: NFS stats, if applicable.

Output File:
Logs are saved to /tmp/Linux_Perf_Monitor_<pid>.log.
Perfmon_aix.py

Description:
This script is designed for AIX systems, focusing on collecting similar metrics as the Linux script, but using commands specific to AIX.

Key Commands:

    uname -a: System info.
    oslevel -s: AIX version and patch level.
    lparstat -i: LPAR information.
    vmstat 1 3: Virtual memory statistics.
    iostat -DlR <disk> 1 1: Disk I/O stats.
    lsvg, lslv: Volume group and logical volume details.
    netstat -v: Network stats.
    ps -ef: Process details.

Output File:
Logs are saved to /tmp/AIX_Perf_Monitor_<pid>.log.
Perfmon_macos.py

Description:
The macOS script collects similar data as the Linux and AIX versions, with a focus on macOS-specific commands.

Key Commands:

    uname -a: System info.
    sw_vers: macOS version information.
    vm_stat: Memory stats.
    sysctl: CPU and memory stats.
    iostat -Id 1 2: Disk I/O stats.
    df -h: Disk usage.
    ps aux: Process stats.
    log show --predicate 'eventMessage contains "error"' --info: Error log collection.

Output File:
Logs are saved to /tmp/MacOS_Perf_Monitor_<pid>.log.
Customization

Each script allows for easy customization by modifying the following parameters at the top of the script:

    RUN_DURATION: Total duration to run the script, in seconds.
    CHECK_INTERVAL: The interval between each data collection cycle, in seconds.

You can also adjust the individual commands if additional metrics or logs are required for your specific use case.
Contribution

If you'd like to contribute to this project by adding additional metrics or improving existing functionality, feel free to open a pull request or submit an issue.
License

This project is licensed under the MIT License.
Author:

    Brian Knight

Let me know if any section needs changes or more details!