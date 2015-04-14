Making Commits and Commit Options
=================================

First we'll talk about the different types of content the `commit` option will accept, then we will discuss the additional arguments that you can use with `commit` to modify the type of commit made to the device(s).  

### Allowed COMMAND arguments for `commit`

The `commit` argument accepts three different types of content, very similar to the `-i`, `operational`, or `shell` options. The three options are:

#### A single set command

A single set command can be sent and committed using this method:

	$ jaide -i 172.25.1.13 commit "set system host-name asdf"

#### Comma separated set commands

Multiple set commands can be sent and committed using a comma separated list (with or without spaces after the commas):

	$ jaide -i 172.25.1.13 commit "set system host-name asdf, set interfaces ge-0/0/0 description asdf"

#### Filepath to a file with set commands

This is the most versatile of the methods. Simply specify a plain text file with set commands each on its own line, and they will be loaded into the device sequentially. While the set commands within the file are loaded sequentially for a single device, if you specify multiple target devices, a process spawns for each device, running simultaneously.  

	$ jaide -i 172.25.1.13 commit ~/Desktop/setlist.txt 
	==================================================
	Results from device: 172.25.1.13
	show | compare:

	[edit logical-systems]
	+  testls {
	+      routing-options {
	+          static {
	+              route 100.0.0.0/16 next-hop [ 1.1.1.1 1.1.1.2 1.1.1.3 ];
	+          }
	+      }
	+  }
	[edit interfaces]
	+   ge-0/0/4 {
	+       description asdf;
	+   }
	[edit routing-options]
	+   /* new annotation here */
	    static { ... }

	Attempting to commit on device: 172.25.1.13
	Commit complete on device: 172.25.1.13

**Note** Both a comma separated list and a file containing set commands support contextual set commands. Consider the following file of set commands: 

	$ cat ~/Desktop/setlist.txt 
	edit logical-systems testls 
	set routing-options static route 100/16 next-hop 1.1.1.1 
	set routing-options static route 100/16 next-hop 1.1.1.2
	set routing-options static route 100/16 next-hop 1.1.1.3
	top
	set interfaces ge-0/0/4 description asdf
	edit routing-options
	annotate static "new annotation here"

The three static route next-hops would be contextually entered into the logical-system `test-ls`, while the interface description on ge-0/0/4 would be added into the base logical-system. Since annotations are context specific, to annotate the `static` stanza of `routing-options` is added only after contextually editing `routing-options`. These commands could also be passed to `commit` in the command line in a comma separated list (although it can get cumbersome quickly):

	$ jaide -i 172.25.1.13 commit "edit logical-systems testls, set routing-options static route 100/16 next-hop 1.1.1.1, set routing-options static route 100/16 next-hop 1.1.1.2, set routing-options static route 100/16 next-hop 1.1.1.3, top, set interfaces ge-0/0/4 description asdf, edit routing-options, annotate static \"new annotation here\""

### Commit Modifiers

Three commit modifiers have currently been implemented into Jaide. They can be used alongside `commit`, and are utilized as follows:

#### Commit Checking

By utilizing `--check` with `commit`, you can issue a commit check only, to ensure syntactical accuracy of your commands, along with the minor Junos configuration checking that a commit check performs. This will not commit the results, but will show you the `show | compare` results, along with the results of a `commit check`. 

An example of commit check succeeding:

	$ jaide -i 172.25.1.13 commit ~/Desktop/setlist.txt --check
	==================================================
	Results from device: 172.25.1.13
	show | compare:

	[edit logical-systems]
	+  testls {
	+      routing-options {
	+          static {
	+              route 100.0.0.0/16 next-hop 1.1.1.1;
	+          }
	+      }
	+  }
	[edit routing-options static]
	     route 192.168.77.0/24 { ... }
	+    route 100.0.0.0/16 next-hop 1.1.1.2;


	Commit check results from: 172.25.1.13
	ok

An example of commit check failing:

	$ jaide -i 172.25.1.13 commit "set interfaces ge-0/0/04.0 family inet filter input asd-filter" --check
	==================================================
	Results from device: 172.25.1.13
	show | compare:

	[edit interfaces]
	+   ge-0/0/4 {
	+       unit 0 {
	+           family inet {
	+               filter {
	+                   input asd-filter;
	+               }
	+           }
	+       }
	+   }


	Commit check results from: 172.25.1.13
	error
	dfwd
	[edit interfaces ge-0/0/4 unit 0 family inet]
	filter
	Referenced filter 'asd-filter' is not defined
	error
	configuration check-out failed

#### Commit Confirming

Commit confirming (`commit -C` or `commit --confirm`) is a useful Junos tool when you are not sure you will maintain connectivity to the device once your commit has completed, or when you are making changes to a critical part of the network and want changes to be confirmed before being accepted. By using `--confirm X` alongside `commit`, the commit you make will be automatically rolled back after X number of **seconds** unless another commit takes place before the time is reached.  

*Note* `commit --confirm` and `commit --at` are mutually exclusive. They both cannot be used at the same time. This is a limitation of Junos.

	$ jaide -i 172.25.1.13 commit "set interfaces ge-0/0/04 description asdf" --confirm 240
	==================================================
	Results from device: 172.25.1.13
	show | compare:

	[edit interfaces]
	+   ge-0/0/4 {
	+       description asdf;
	+   }

	Attempting to commit confirmed on device: 172.25.1.13
	Commit complete on device: 172.25.1.13. It will be automatically rolled back in 4 minutes, unless you commit again.

At this point, it is required to commit again against the device (a blank commit, since you don't want any other changes added). This is where the third modifier comes in.

#### Commit Blank

Commit Blank (`--blank`, `--no-blank`) will simply log into the device and issue a commit, without sending any set commands. This can be very useful to send a confirmation for a commit confirm that is pending to be rolled back.  

**Note** Commit Blank doesn't actually truly make commit without sending any set commands, as Junos doesn't support this over netconf. To perform a blank commit we send one command: `annotate system`. This won't overwrite any annotation already on the system stanza, and functionally makes a blank commit

	$ jaide -i 172.25.1.13 commit --blank
	==================================================
	Results from device: 172.25.1.13
	show | compare:


	Attempting to commit on device: 172.25.1.13
	Commit complete on device: 172.25.1.13

This will perform a blank command, even with nonsense passed to `commit`:

	$ jaide -i 172.25.1.13 commit "asdnioqwnioqwdnasiodnas" --blank
	==================================================
	Results from device: 172.25.1.13
	show | compare:


	Attempting to commit on device: 172.25.1.13
	Commit complete on device: 172.25.1.13

Still sending a blank commit, even with a valid command:

	$ jaide -i 172.25.1.13 commit "set interfaces ge-0/0/0 description asdf" --blank 
	==================================================
	Results from device: 172.25.1.13
	show | compare:


	Attempting to commit on device: 172.25.1.13
	Commit complete on device: 172.25.1.13

#### Commit At  

Commit at (`commit -a`, or `commit --at`)can be used to delay the commit operation to a later time/date. One of two formats should be used for the commit --at argument:  

* hh:mm[:ss]  
* yyyy-mm-dd hh:mm[:ss]  

*NOTE* `commit --at` and `commit --comfirm` are mutually exclusive and connect be used together. Each of them can be used with any other commit modifier however.

Example output:  

	$ jaide -i 192.168.50.95 -u root -p root123 commit "set interfaces ge-0/0/0 description asdfeqwewrwersdfsdf" --at "2015-04-30 01:15"
	==================================================
	Results from device: 192.168.50.95

	show | compare:

	[edit interfaces ge-0/0/0]
	+   description asdfeqwewrwersdfsdf;

	Attempting to commit on device: 192.168.50.95
	fpc0
	configuration check succeeds
	commit at will be executed at 2015-04-30 01:15:00 CDT

	Commit complete on device: 192.168.50.95

#### Comment Comment  

Commit comment (`commit -c` or `commit --comment`) is a useful modifier that allows a string to be put into the `show system commit` log next to the corresponding commit. The syntax is as follows:

	$ jaide -i 192.168.50.95 -u root -p root123 commit "set interfaces ge-0/0/0 description asdf" --comment "My super commit!"

#### Commit Sync

Commit sync (`--sync`, `--no-sync`)is useful flag to use on multi-RE systems (EX VC's, high-end MX's, etc), as it ensures that both RE's perform the commit at the same time and the config is pushed from master to backup at the time of commit.  Example syntax:

	$ jaide -i 192.168.50.95 -u root -p root123 commit "set interfaces ge-0/0/0 description asdf" --sync
