Making Commits and Commit Options
=================================

First we'll talk about the different types of content the `-s` option will accept, then we will discuss the additional arguments that you can use with `-s` to modify the commit made to the device(s).  

### Allowed strings for `-s`

The `-s` argument accepts three different types of content, very similar to the `-i`, `-c`, or `--shell` arguments. The three options are:

#### A single set command

A single set command can be sent and committed using this method:

	$ python jaide.py -i 172.25.1.13 -s "set system host-name asdf"

#### Comma separated set commands

Multiple set commands can be sent and committed using a comma separated list (with or without spaces after the commas):

	$ python jaide.py -i 172.25.1.13 -s "set system host-name asdf, set interfaces ge-0/0/0 description asdf"

#### Filepath to a file with set commands

This is the most versatile of the methods. Simply specify a plain text file with set commands each on its own line, and they will be loaded into the device sequentially. While the set commands within the file are loaded sequentially for a single device, if you specify multiple target devices, a process spawns for each device, running simultaneously.  

	$ python jaide.py -i 172.25.1.13 -s ~/Desktop/setlist.txt 
	==================================================
	Results from device: 172.25.1.13
	Comparison results:

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

The three static route next-hops would be contextually entered into the logical-system `test-ls`, while the interface description on ge-0/0/4 would be added into the base logical-system. Since annotations are context specific, to annotate the `static` stanza of `routing-options` is added only after contextually editing `routing-options`. These commands could also be passed to `-s` in the command line in a comma separated list (although it can get cumbersome quickly):

	$ python jaide.py -i 172.25.1.13 -s "edit logical-systems testls, set routing-options static route 100/16 next-hop 1.1.1.1, set routing-options static route 100/16 next-hop 1.1.1.2, set routing-options static route 100/16 next-hop 1.1.1.3, top, set interfaces ge-0/0/4 description asdf, edit routing-options, annotate static \"new annotation here\""

### Commit Modifiers

Three commit modifiers have currently been implemented into Jaide. They can be used alongside `-s`, and are utilized as follows:

#### Commit Checking

By utilizing `--check` with `-s`, you can issue a commit check only, to ensure syntactical accuracy of your commands, along with the minor Junos configuration checking that a commit check performs. This will not commit the results, but will show you the `show | compare` results, along with the results of a `commit check`. 

An example of commit check succeeding:

	$ python jaide.py -i 172.25.1.13 -s ~/Desktop/setlist.txt --check
	==================================================
	Results from device: 172.25.1.13
	Comparison results:

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

	$ python jaide.py -i 172.25.1.13 -s "set interfaces ge-0/0/04.0 family inet filter input asd-filter" --check
	==================================================
	Results from device: 172.25.1.13
	Comparison results:

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

Commit confirming is a useful Junos tool when you are not sure you will maintain connectivity to the device once your commit has completed, or when you are making changes to a critical part of the network and want changes to be confirmed before being accepted. By using `--confirmed X` alongside `-s`, the commit you make will be automatically rolled back after X number of minutes unless another commit takes place before the time is reached. 

	$ python jaide.py -i 172.25.1.13 -s "set interfaces ge-0/0/04 description asdf" --confirmed 4
	==================================================
	Results from device: 172.25.1.13
	Comparison results:

	[edit interfaces]
	+   ge-0/0/4 {
	+       description asdf;
	+   }

	Attempting to commit confirmed on device: 172.25.1.13
	Commit complete on device: 172.25.1.13. It will be automatically rolled back in 4 minutes, unless you commit again.

At this point, it is required to either run the same command again to confirm the commit or issue a blank commit, which is where the third and final modifier comes in.

#### Commit Blank

Commit Blank will simply log into the device and issue a commit, without sending any set commands. This can be very useful to send a confirmation for a commit confirm that is pending to be rolled back.  

**Note** Commit Blank is unique in that it does not require setting the `-s` argument to be used, but it won't hurt anything to specify both `-s` and `--blank`. If you do use both `-s` and `--blank`, there must be a string passed along with `-s`. It can be an empty string or anything, it doesn't matter, it won't be taken into account when `--blank` is specified. All of these examples do the same thing, which is a blank commit:

	$ python jaide.py -i 172.25.1.13 --blank
	==================================================
	Results from device: 172.25.1.13
	Comparison results:


	Attempting to commit on device: 172.25.1.13
	Commit complete on device: 172.25.1.13

With `-s`:

	$ python jaide.py -i 172.25.1.13 -s "" --blank
	==================================================
	Results from device: 172.25.1.13
	Comparison results:


	Attempting to commit on device: 172.25.1.13
	Commit complete on device: 172.25.1.13

This will perform a blank command, even with nonsense passed to `-s`:

	$ python jaide.py -i 172.25.1.13 --blank -s "asdnioqwnioqwdnasiodnas"
	==================================================
	Results from device: 172.25.1.13
	Comparison results:


	Attempting to commit on device: 172.25.1.13
	Commit complete on device: 172.25.1.13

Still sending a blank commit, even with a valid command:

	$ python jaide.py -i 172.25.1.13 --blank -s "set interfaces ge-0/0/0 description asdf"
	==================================================
	Results from device: 172.25.1.13
	Comparison results:


	Attempting to commit on device: 172.25.1.13
	Commit complete on device: 172.25.1.13