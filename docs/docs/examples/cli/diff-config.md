Comparing Config Differences Between two Devices
================================

We use the standard python library `difflib` to run a comparison between the configuration of two devices. The output of this comparison is very similar to that of the change control system `git`. Therefore if it looks a little confusing to you, try checking out [this document](http://www.git-tower.com/learn/ebook/command-line/advanced-topics/diffs) for an explanation.

This actively pulls the running configuration from the devices for this comparison. There are options for this command, as follows:  

| Option | Full Name Flag | Description |  
| ------ | -------------- | ----------- |  
| -i 	| --second-host | The second host to compare against. This is required. The connection will use the same username and password as the first host by default. |  
| -m 	| --mode | This is how to view the differences, can be either `set` or `stanza`. Defaults to `set`. |  
| -u 	| --second-username | The username to use for the secondary device. |  
| -p 	| --second-password | The password to use for the secondary device. |  


## Example

	$ jaide  -i 192.168.50.95 -u root -p root123 diff -i 192.168.50.99 -m stanza
	==================================================
	Results from device: 192.168.50.95

	--- 192.168.50.95

	+++ 192.168.50.99

	@@ -1,58 +1,119 @@

	-version 12.3R3.4;
	+version 12.1X44-D35.5;
	 system {
	-    host-name Bender;
	+    host-name The-Professor;
	     time-zone America/Chicago;
	+    name-server {
	+        8.8.8.8;
	+        8.8.4.4;
	     }
	     services {
	-        ssh;
	-        netconf {
	-            ssh;
	+        ssh {
	+            protocol-version v2;
	+            max-sessions-per-connection 10;
	+            client-alive-count-max 6;
	+            client-alive-interval 5;
	+        }
	
	...
	
	[truncated for brevity]
