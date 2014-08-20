Getting Health Checks
=====================  
Using the `--health` argument on the command line with jaide.py will gather the following information. 

* Chassis Alarms
* System Alarms
* Routing Engine Information (CPU/RAM utilization)
* Last reboot time and reason.
* The top 5 busiest processes on the device. 

**Single Device**  

	$ python jaide.py -i 172.25.1.21 --health -u root -p root123
	==================================================
	Results from device: 172.25.1.21

	Chassis Alarms: 
		No chassis alarms active.

	System Alarms: 
		No system alarms active.

	Routing Engine Information:
	RE0 Status: 	OK
		Mastership: 	master
		Used Memory %: 	47
		CPU Temp: 	35 degrees C / 95 degrees F
		Idle CPU%: 	100
		Serial Number: 	***********
		Last Reboot: 	0x2:watchdog 
		Uptime: 	24 days, 9 hours, 31 minutes, 43 seconds

	Top 5 busiest processes:
	  PID USERNAME  THR PRI NICE   SIZE    RES STATE    TIME   WCPU COMMAND
	   11 root        1 171   52     0K    16K RUN    539.9H 85.84% idle
	39896 root        1 103    0 37196K 24256K select   0:02 54.97% mgd
	39893 root        1  97    0  7592K  2956K select   0:00  4.90% sshd
	 1301 root        1   8    0 86780K 24508K nanslp  24.2H  1.71% pfem
	  930 root        1  99    0 12604K  6920K select   0:34  0.20% eventd

**Multiple Devices**  

	$ python jaide.py -i ~/desktop-link/iplist.txt --health -u root -p root123
	==================================================
	Results from device: 172.25.1.22

	Chassis Alarms: 
		No chassis alarms active.

	System Alarms: 
		Minor Alarm 		2014-07-09 18:29:30 UTC
		RIPng Routing Protocol usage requires a license
		Minor Alarm 		2014-07-09 18:29:30 UTC
		OSPFv3 Routing Protocol usage requires a license
		Minor Alarm 		2014-07-09 18:29:30 UTC
		BGP Routing Protocol usage requires a license

	Routing Engine Information:
	RE0 Status: 	OK
		Mastership: 	master
		Used Memory %: 	38
		CPU Temp: 	36 degrees C / 96 degrees F
		Idle CPU%: 	97
		Serial Number: 	***********
		Last Reboot: 	Router rebooted after a normal shutdown.
		Uptime: 	24 days, 9 hours, 36 minutes, 6 seconds

	Top 5 busiest processes:
	  PID USERNAME  THR PRI NICE   SIZE    RES STATE    TIME   WCPU COMMAND
	   11 root        1 171   52     0K    16K RUN    539.2H 91.06% idle
	40264 root        1 132    0 28296K 17584K select   0:01 47.15% mgd
	40261 root        1  98    0  7244K  2684K select   0:00  6.66% sshd
	40263 root        1   8    0  2552K  1252K wait     0:00  0.51% sh
	 1068 root        1   8    0 85104K 12256K nanslp  21.3H  0.10% pfem

	==================================================
	Results from device: 172.25.1.21

	Chassis Alarms: 
		No chassis alarms active.

	System Alarms: 
		No system alarms active.

	Routing Engine Information:
	RE0 Status: 	OK
		Mastership: 	master
		Used Memory %: 	47
		CPU Temp: 	35 degrees C / 95 degrees F
		Idle CPU%: 	82
		Serial Number: 	***********
		Last Reboot: 	0x2:watchdog 
		Uptime: 	24 days, 9 hours, 35 minutes, 56 seconds

	Top 5 busiest processes:
	  PID USERNAME  THR PRI NICE   SIZE    RES STATE    TIME   WCPU COMMAND
	   11 root        1 171   52     0K    16K RUN    540.0H 86.87% idle
	39909 root        1 101    0 37196K 24256K select   0:02 55.32% mgd
	39906 root        1  97    0  7592K  2960K select   0:00  4.90% sshd
	 1301 root        1   8    0 86780K 24508K nanslp  24.2H  1.07% pfem
	  930 root        1  98    0 12604K  6920K select   0:34  0.20% eventd

	==================================================
	Results from device: 172.25.1.51

	Chassis Alarms: 
		No chassis alarms active.

	System Alarms: 
		No system alarms active.

	Routing Engine Information:
	RE0 Status: 	OK
		Mastership: 	backup
		Used Memory %: 	28
		CPU Temp: 	35 degrees C / 95 degrees F
		Idle CPU%: 	95
		Serial Number: 	***********
		Last Reboot: 	Router rebooted after a normal shutdown.
		Uptime: 	61 days, 21 hours, 32 minutes, 35 seconds

	RE1 Status: 	OK
		Mastership: 	master
		Used Memory %: 	29
		CPU Temp: 	36 degrees C / 96 degrees F
		Idle CPU%: 	94
		Serial Number: 	***********
		Last Reboot: 	Router rebooted after a normal shutdown.
		Uptime: 	61 days, 21 hours, 32 minutes, 35 seconds

	Top 5 busiest processes:
	  PID USERNAME  THR PRI NICE   SIZE    RES STATE    TIME   WCPU COMMAND
	   11 root        1 171   52     0K  3536K RUN    1154.0 81.05% idle
	15635 root        1 103    0 25856K 19392K select   0:02 68.63% mgd
	15632 root        1 100    0  6584K  3012K select   0:00  5.92% sshd
	 1065 root        1   8    0   134M 13856K nanslp 135.6H  1.07% pfem
	15634 root        1   8    0  2244K  1416K wait     0:00  0.70% sh

	==================================================
	Results from device: 172.25.1.61

	Chassis Alarms: 
		No chassis alarms active.

	System Alarms: 
		No system alarms active.

	Routing Engine Information:
		Used Memory %: 	67
		CPU Temp: 	43 degrees C / 109 degrees F
		Idle CPU%: 	87
		Serial Number: 	***********
		Last Reboot: 	0x200:normal shutdown
		Uptime: 	70 days, 19 hours, 26 minutes, 7 seconds

	Top 5 busiest processes:
	  PID USERNAME  THR PRI NICE   SIZE    RES STATE  C   TIME   WCPU COMMAND
	   22 root        1 171   52     0K    16K RUN    0 1231.2 7518.75% idle: cpu0
	   23 root        1 -40 -159     0K    16K WAIT   0 126:11 7518.75% swi2: netisr 0
	 1293 root        5  76    0   531M 79088K select 0 1888.2 96.92% flowd_octeon_hm
	61699 root        1 132    0 24264K  1872K CPU0   0   0:00 23.29% top
	61697 root        1 132    0 38696K 22852K select 0   0:03 22.51% mgd