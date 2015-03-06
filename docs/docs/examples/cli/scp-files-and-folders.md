Using SCP to copy files and folders
===================================

Our implementation uses paramiko as a transport channel, with the SCP module handling the actual transfer. This means that the `--scp` argument must be qualified with one of two methods: `push` or `pull`. This explicitly states the direction of the file transfer. The source and destination file(s)/folder must also be specified immediately after the direction, which is detailed below in the examples. 

One of the benefits of using the `--scp` function with Jaide is that you can send push or pull files to/from many devices at the same time. We use multiprocessing to run many scp instances simultaneously, carrying out the copy commands for up to 2*(number of CPU cores) devices at the same time. If you are receiving a file or folder from multiple remote Junos devices, the received name will be prepended with the IP address of the device it was received from to help distinguish them.  

When using the Jaide to receive or push a file/folder to/from a single remote device, a callback function is used to show you the progress of the current file that is being copied.  

**Home Directory Alias -** Command line users running jaide.py will find that the `~` home directory alias will work. Unfortunately, this ability is lost in the GUI. Links will still be followed in the GUI, but you cannot use the `~` shortcut.  

### Pulling remote files and folders to the local device

In the first example, we pull the `/var/log/pfed` log file from one remote device.

	$ python jaide.py -u operate -p Op3r4t3 -i 172.25.1.13 --scp pull /var/log/pfed ~/desktop-link/scp/
	==================================================
	Results from device: 172.25.1.13
	Retrieving 172.25.1.13:/var/log/pfed, and putting it in /Users/nprintz/desktop-link/scp/pfed

	Transferred 100% of the file /Users/nprintz/desktop-link/scp/pfed                                                       
	Received /var/log/pfed from 172.25.1.13.



In this example, we try to copy the `/var/log` folder from a device to the local machine, but we failed to copy all files due to a permissions issue. 

	$ python jaide.py -i 172.25.1.21 --scp pull /var/log ~/desktop-link/scp/
	==================================================
	Results from device: 172.25.1.21
	Retrieving 172.25.1.21:/var/log, and putting it in /Users/nprintz/desktop-link/scp/log


	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/chassisd
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/mastership
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/inventory
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/eccd
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/dfwc
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/dcd
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/cosd
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/authd_sdb.log
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/authd_profilelib
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/authd_libstats
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/ifstraced
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/autodlog
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/pgmd
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/messages
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/interactive-commands
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/default-log-messages
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/gres-tp
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/license
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/wtmp
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/pfed
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/snapshot
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/install
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/ospf3trace
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/httpd.log
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/httpd.log.old
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/shadow.log
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/messages.0.gz
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/messages.1.gz
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/interactive-commands.0.gz
	Transferred 100% of the file /Users/nprintz/desktop-link/scp/log/ebgp_trace
	!!! Error during copy from 172.25.1.21. Some files may have failed to transfer. SCP Module error:                       
	scp: /var/log/escript.log: Permission denied
	scp: /var/log/op-script.log: Permission denied
	T1371178881 0 1371178824 0
	!!!

Here is copying the /var/log file from multiple devices successfully:

	$ python jaide.py -i ~/desktop-link/iplist.txt --scp pull /var/log ~/desktop-link/scp/
	==================================================
	Results from device: 172.25.1.60
	Retrieving 172.25.1.60:/var/log, and putting it in /Users/nprintz/desktop-link/scp/172.25.1.60_log
	Received /var/log from 172.25.1.60.

	==================================================
	Results from device: 172.25.1.61
	Retrieving 172.25.1.61:/var/log, and putting it in /Users/nprintz/desktop-link/scp/172.25.1.61_log
	Received /var/log from 172.25.1.61.

	==================================================
	Results from device: 172.25.1.51
	Retrieving 172.25.1.51:/var/log, and putting it in /Users/nprintz/desktop-link/scp/172.25.1.51_log
	Received /var/log from 172.25.1.51.
	
	==================================================
	Results from device: 172.25.1.22
	Retrieving 172.25.1.22:/var/log, and putting it in /Users/nprintz/desktop-link/scp/172.25.1.22_log
	Received /var/log from 172.25.1.22.

### Pushing local files and folders to remote device(s)

Here is pushing a single file to a single remote device:

	$ python jaide.py -i 172.25.1.21 --scp push ~/desktop-link/scp/template /var/tmp
	Pushing /Users/nprintz/desktop-link/scp/template to 172.25.1.21:/var/tmp/

	Transferred 100% of the file template                                                                                   
	Pushed /Users/nprintz/desktop-link/scp/template to 172.25.1.21:/var/tmp/

	$ python jaide.py  -i 172.25.1.21 -shell "ls /var/tmp"
	==================================================
	Results from device: 172.25.1.21
	> ls /var/tmp

	.DS_Store	.snap		gres-tp		rtsdb		template
	.localized	event_tags.php	my-new-file	stp.slax

Here is pushing a directory to a remote device:

	$ python jaide.py -i 172.25.1.21 --scp push ~/desktop-link/scp/172.25.1.21_log/ /var/tmp 
	==================================================
	Results from device: 172.25.1.21
	Pushing /Users/nprintz/desktop-link/scp/172.25.1.21_log to 172.25.1.21:/var/tmp/

	Transferred 100% of the file authd_libstats                             
	Transferred 100% of the file authd_profilelib                           
	Transferred 100% of the file authd_sdb.log                              
	Transferred 100% of the file autodlog                                   
	Transferred 100% of the file chassisd                                   
	Transferred 100% of the file cosd                                       
	Transferred 100% of the file dcd                                        
	Transferred 100% of the file default-log-messages                       
	Transferred 100% of the file dfwc                                       
	Transferred 100% of the file ebgp_trace                                 
	Transferred 100% of the file eccd                                       
	Transferred 100% of the file gres-tp                                    
	Transferred 100% of the file httpd.log                                  
	Transferred 100% of the file httpd.log.old                              
	Transferred 100% of the file ifstraced                                  
	Transferred 100% of the file install                                    
	Transferred 100% of the file interactive-commands                       
	Transferred 100% of the file interactive-commands.1.gz                  
	Transferred 100% of the file interactive-commands.2.gz                  
	Transferred 100% of the file interactive-commands.3.gz                  
	Transferred 100% of the file interactive-commands.4.gz                               
	Transferred 100% of the file inventory                                  
	Transferred 100% of the file license                                    
	Transferred 100% of the file mastership                                 
	Transferred 100% of the file messages                                   
	Transferred 100% of the file messages.1.gz                              
	Transferred 100% of the file messages.2.gz                              
	Transferred 100% of the file messages.3.gz                              
	Transferred 100% of the file messages.4.gz                                                      
	Transferred 100% of the file ospf3trace                                 
	Transferred 100% of the file pfed                                       
	Transferred 100% of the file pgmd                                       
	Transferred 100% of the file shadow.log                                 
	Transferred 100% of the file shadow.log.0.gz                            
	Transferred 100% of the file shadow.log.1.gz                            
	Transferred 100% of the file snapshot                                   
	Transferred 100% of the file testforqc                                  
	Transferred 100% of the file wtmp                                       
	Transferred 100% of the file wtmp.0.gz                                  
	Transferred 100% of the file wtmp.1.gz                                  
	Transferred 100% of the file wtmp.2.gz                                  
	Transferred 100% of the file wtmp.3.gz                                  
	Transferred 100% of the file wtmp.4.gz                                  
	Pushed /Users/nprintz/desktop-link/scp/172.25.1.21_log to 172.25.1.21:/var/tmp/



Here is pushing a file to multiple remote devices:

	$ python jaide.py -i ~/desktop-link/iplist.txt --scp push ~/desktop-link/scp/template /var/tmp
	==================================================
	Results from device: 172.25.1.21
	Pushing /Users/nprintz/desktop-link/scp/template to 172.25.1.21:/var/tmp/
	Pushed /Users/nprintz/desktop-link/scp/template to 172.25.1.21:/var/tmp/

	==================================================
	Results from device: 172.25.1.22
	Pushing /Users/nprintz/desktop-link/scp/template to 172.25.1.22:/var/tmp/
	Pushed /Users/nprintz/desktop-link/scp/template to 172.25.1.22:/var/tmp/

	==================================================
	Results from device: 172.25.1.51
	Pushing /Users/nprintz/desktop-link/scp/template to 172.25.1.51:/var/tmp/
	Pushed /Users/nprintz/desktop-link/scp/template to 172.25.1.51:/var/tmp/

	==================================================
	Results from device: 172.25.1.61
	Pushing /Users/nprintz/desktop-link/scp/template to 172.25.1.61:/var/tmp/
	Pushed /Users/nprintz/desktop-link/scp/template to 172.25.1.61:/var/tmp/

