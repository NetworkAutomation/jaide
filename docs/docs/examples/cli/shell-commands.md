Using Shell Commands
====================  

## Shell Commands

Here we use the shell argument to simply print the working directory when logging in as root. 

	$ python jaide.py -i 172.25.1.21 --shell pwd
	==================================================
	Results from device: 172.25.1.21
	> pwd

	/var/root

Here we use the shell argument to print the working directory, change directories and print again.

	$ python jaide.py -i 172.25.1.21 --shell "pwd,cd /var/tmp, pwd"
	==================================================
	Results from device: 172.25.1.21
	> pwd

	/var/root

	> cd /var/tmp


	> pwd

	/var/tmp

Here we use a file containing the following contents:

	pwd 
	cd /var/tmp
	pwd
	ls -lap
	touch my-new-file
	ls -lap

These are carried out sequentially with session based context:

	$ python jaide.py -i 172.25.1.21 --shell ~/Desktop/shelllist.txt 
	==================================================
	Results from device: 172.25.1.21
	> pwd

	/var/home/operate

	> cd /var/tmp


	> pwd

	/var/tmp

	> ls -lap

	total 220
	drwxrwxrwt   5 root     field   1536 Jul  2 13:27 ./
	drwxr-xr-x  33 root     wheel    512 Jun 13  2013 ../
	-rw-r--r--   1 operate  field      0 Dec 26  2012 .localized
	drwxrwxr-x   2 root     wheel    512 Dec 31  2004 .snap/
	drwxr-xr-x   2 root     field    512 Jun 13  2013 gres-tp/
	drwxr-xr-x   2 root     field    512 Jun 13  2013 rtsdb/

	> touch my-new-file


	> ls -lap

	total 220
	drwxrwxrwt   5 root     field   1536 Jul 10 06:54 ./
	drwxr-xr-x  33 root     wheel    512 Jun 13  2013 ../
	-rw-r--r--   1 operate  field      0 Dec 26  2012 .localized
	drwxrwxr-x   2 root     wheel    512 Dec 31  2004 .snap/
	drwxr-xr-x   2 root     field    512 Jun 13  2013 gres-tp/
	-rw-r--r--   1 operate  field      0 Jul 10 06:54 my-new-file
	drwxr-xr-x   2 root     field    512 Jun 13  2013 rtsdb/