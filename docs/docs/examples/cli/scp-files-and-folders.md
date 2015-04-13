Using SCP to copy files and folders
===================================

Our implementation uses paramiko as a transport channel, with the SCP module handling the actual transfer. You *must* specify the direction of the copy (it is the command name) for the transfer: `push` or `pull`. This explicitly states the direction of the file transfer.  

Both the `pull` and `push` commands have the same required arguments, in the following format:  

	jaide push [OPTION] SOURCE_FILEPATH DEST_FILEPATH

in the above case, we'd be copying a file or directory from the local system to one or more remote junos devices. the DEST_FILEPATH would be a Junos recognized folder path, such as `/var/tmp`. The `[OPTION]` can be a single optional argument `--no-progress`, to disable the output of the progress of the transfer as it happens. This does not apply to when copying to/from multiple devices, as this is suppressed automatically. If it wasn't, the output from each device would be jumbled up and printed simultaneously.  

One of the benefits of using the `pull` or `push` functions with Jaide is that you can send files to/from many devices at the same time. We use multiprocessing to run many scp instances simultaneously, carrying out the copy commands for up to 2*(number of CPU cores) devices at the same time. If you are receiving a file or folder from multiple remote Junos devices, the received name will be prepended with the IP address of the device it was received from to help distinguish them.  

### Pulling remote files and folders to the local device

In the first example, we pull the `/var/log/pfed` log file from one remote device.

	$ jaide -u username -p password -i 172.25.1.13 pull /var/log/pfed ~/desktop-link/scp/
	==================================================
	Results from device: 172.25.1.13
	Retrieving 172.25.1.13:/var/log/pfed, and putting it in /Users/nprintz/desktop-link/scp/pfed

	Transferred 100% of the file /Users/nprintz/desktop-link/scp/pfed                                                       
	Received /var/log/pfed from 172.25.1.13.



In this example, we try to copy the `/var/log` folder from a device to the local machine, but we failed to copy all files due to a permissions issue. 

	$ jaide -i 172.25.1.21 pull /var/log ~/desktop-link/scp/
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

Here is copying the `/var/log` folder from multiple devices successfully:

	$ jaide -i ~/desktop-link/iplist.txt pull /var/log ~/desktop-link/scp/
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

	$ jaide -i 172.25.1.21 push ~/desktop-link/scp/template /var/tmp
	==================================================
	Results from device: 172.25.1.21
	Pushing /Users/nprintz/desktop-link/scp/template to 172.25.1.21:/var/tmp/

	Transferred 100% of the file template                                                                                   
	Pushed /Users/nprintz/desktop-link/scp/template to 172.25.1.21:/var/tmp/

	$ jaide  -i 172.25.1.21 -shell "ls /var/tmp"
	==================================================
	Results from device: 172.25.1.21
	> ls /var/tmp

	.DS_Store	.snap		gres-tp		rtsdb		template
	.localized	event_tags.php	my-new-file	stp.slax

Here is pushing a directory to a remote device:

	$ jaide -i 172.25.1.21 push ~/desktop-link/scp/172.25.1.21_log/ /var/tmp 
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

	$ jaide -i ~/desktop-link/iplist.txt push ~/desktop-link/scp/template /var/tmp
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

