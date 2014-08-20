""" jgui.py
	This python file is used to spawn the GUI that can be used to call jaide.py
"""
try:
    ### Tkinter related imports.
    import Tkinter as tk
    import tkFileDialog
    import tkMessageBox  # to prompt users during input validation errors
    import ttk  # Used for separators between frames of the UI.
    import Pmw  # Pmw is the extended menuwidget option giving us the ability to call a function when a option is chosen from the menu.
    ### Processing and queueing
    import subprocess  # Used for opening help file with the browser. 
    import Queue
    # In temrs of JGUI, we use multiprocessing to enable freeze_support. The worker_thread class uses multiprocessing 
    # further to run concurrent instances of the Jaide script when manipulating multiple devices. 
    import multiprocessing as mp
    ### Basic functions and manipulation. 
    import webbrowser  # for opening URL in a web browser. 
    import re  # for regex testing in input validation.
    import os  # needed for opening files, file validation, getting directory names, etc.
    import sys  # needed for checking OS type.
    import base64  # for encoding/decoding text. 
    import time  # needed to sleep very quickly when updating the UI, to prevent artifacting. 
    ### The following imports are modules that we have written. 
    import jaide
    # the jgui_widgets module extends basic Tkinter widgets for expressed use within the Jaide GUI
    from jgui_widgets import JaideEntry, JaideCheckbox, AutoScrollbar
    from worker_thread import WorkerThread  # Used on exeting the 'Run Script' button to create a thread and run 
    from module_locator import module_path  # Used to find the location of the running module, whether it is compiled or not, across all platforms. 
except ImportError as e:
    print "Failed to import one or more packages! Non-standard packages for the GUI include:\nPMW\t\thttp://pmw.sourceforge.net/\n\nScript Error:\n"
    raise e

# TODO: make Script output non-editable, but still selectable for copying.
# TODO: add headers to the sections of the GUI / add coloring or styling.  - Attempted, couldn't get menuoption to work, or checkboxes on mac. 

class JaideGUI(tk.Tk):
    """ The JaideGUI class inherits the properties of the Tkinter.Tk class. This class encapsulates the entire methodology for 
        creating the visual representation seen by the user. Some functionality is enhanced with the use of other classes that 
        are imported and used, including WorkerThread (for running the jaide.py script and handling output gathering) and 
        AutoScrollbar (for putting scrollbars on the output_area text entry widget. 
    """
    def __init__(self, parent):
        """ Purpose: This is the initialization function for creating and showing the GUI. 
        """
        tk.Tk.__init__(self, parent)
        self.parent = parent

        self.grid()
        self.wm_title("Jaide GUI")
        self.focus_force()

        ### Argument and option lists for user input
        # arguments that require extra input
        self.yes_options = ["Operational Command(s)", "Set Command(s)", "Shell Command(s)", "SCP Files"]
        # arguments that don't require extra input
        self.no_options = ["Interface Errors", "Health Check", "Device Info"]
        # List of argument options
        self.options_list = ["Operational Command(s)", "Set Command(s)", "Shell Command(s)", "SCP Files", "------", "Device Info", "Health Check", "Interface Errors"]
        
        # Dictionary converting option_menu's displayed options with jaide's actual argument flags
        self.option_conversion = {
                "Device Info" : jaide.dev_info,
                "Health Check" : jaide.health_check,
                "Interface Errors" : jaide.int_errors,
                "Operational Command(s)" : jaide.multi_cmd, 
                "SCP Files" : jaide.copy_file,
                "Set Command(s)" : jaide.make_commit,
                "Shell Command(s)" : jaide.multi_cmd
            }
        # Dictionary for retrieving the help text based on the command name.
        self.help_conversion = {
                "Device Info" : "Quick Help: Device Info pulls some baseline information from the device(s), including Hostname, Model, Junos Version, and Chassis Serial Number.",
                "Health Check" : "Quick Help: Health Check runs multiple commands to get routing-engine CPU/memory info, busy processes, temperatues, and alarms. The output will likely show the mgd process using high CPU, this is normal due to the execution of the script logging in and running the commands.",
                "Interface Errors" : "Quick Help: Interface Errors will tell you of any input or output errors on active interfaces.",
                "Operational Command(s)" : "Quick Help: Run one or more operational command(s) against the device(s). This can be any non-interactive command(s) that can be run from operational mode. This includes show, request, traceroute, op scripts, etc.", 
                "SCP Files" : "Quick Help: SCP file(s) or folder(s) to or from one or more devices. Specify a source and destination file or folder. If Pulling, the source is the remote file/folder, and the destination is the local folder you are putting them. If Pushing, the source is the local file/folder, and the destination would the folder to put them on the remote device. Note, the '~' home directory link can not be used! ",
                "Set Command(s)" : "Quick Help: A single or multiple set commands that will be sent and committed to the device(s). There are three optional commit modifiers, which can be used to do a commit check, commit confirmed, or blank commit. More information in the help files.",
                "Shell Command(s)" : "Quick Help: Send one or more shell commands to the device(s). Be wary when sending shell commands, you can make instant changes or potentially harm the networking device. Care should be taken."
            }
        
        # stdout_queue is the output queue that the WorkerThread class will put output to.
        self.stdout_queue = Queue.Queue()
        # thread will be the WorkerThread instantiation.
        self.thread = ""
        # frames_shown boolean for keeping track if the upper options of the GUI are shown or not. 
        self.frames_shown = True

        ### CREATE THE TOP MENUBAR OPTIONS
        self.menubar = tk.Menu(self)
        # tearoff=0 is to prohibit windows users from being able to pop out the menus. 
        self.menu_file = tk.Menu(self.menubar, tearoff=0)
        self.menu_help = tk.Menu(self.menubar, tearoff=0)

        self.menubar.add_cascade(menu=self.menu_file, label="File")
        self.menubar.add_cascade(menu=self.menu_help, label="Help ")  # Added space after Help to prevent OSX from putting spotlight in

        # Create the File menu and appropriate keyboard shortcuts.
        self.menu_file.add_command(label="Save Template", command=lambda: self.save_template(None), accelerator='Ctrl-S')
        self.bind_all("<Control-s>", self.save_template)
        self.menu_file.add_command(label="Open Template", command=lambda: self.open_template(None), accelerator='Ctrl-O')
        self.bind_all("<Control-o>", self.open_template)
        self.menu_file.add_separator()
        self.menu_file.add_command(label="Clear Fields", command=lambda: self.clear_fields(None), accelerator='Ctrl-F')
        self.bind_all("<Control-f>", self.clear_fields)
        self.menu_file.add_command(label="Clear Output", command=lambda: self.clear_output(None), accelerator='Ctrl-W')
        self.bind_all("<Control-w>", self.clear_output)
        self.menu_file.add_command(label="Run Script", command=lambda: self.go(None), accelerator='Ctrl-R')
        self.bind_all("<Control-r>", self.go)
        self.menu_file.add_separator()
        self.menu_file.add_command(label="Quit", command=lambda: self.quit(None), accelerator='Ctrl-Q')
        self.bind_all("<Control-q>", self.quit)

        # Create the Help menu
        self.menu_help.add_command(label="About", command=self.show_about)
        self.menu_help.add_command(label="Help Text", command=self.show_help)
        self.menu_help.add_command(label="Examples", command=self.show_examples)

        # Add the menubar in.
        self.config(menu=self.menubar)

        ############################################
        # GUI frames, and all user entry widgets   #
        ############################################
        ### FRAME INITIALIZATION]
        
        # IP+Cred+Sep Frame
        # Had to do this because Grid was treating all of the frames & separators as 1x1 units
        # so without combining creds & ip in a single container frame the IP side was subject to resizing
        # based on the other frames
        self.ip_cred_frame = tk.Frame(self)

        # IP frame
        self.ip_frame = tk.Frame(self.ip_cred_frame)
        # Credentials frame
        self.creds_frame = tk.Frame(self.ip_cred_frame)
        # write to file frame
        self.wtf_frame = tk.Frame(self)
        # Options frame
        self.options_frame = tk.Frame(self)
        # Help frame
        self.help_frame = tk.Frame(self)
        # go button frame
        self.buttons_frame = tk.Frame(self)
        # output area frame
        self.output_frame = tk.Frame(self, bd=3, relief="groove")

        ##### Target device Section
        # string of actual IP or the file containing list of IPs
        self.ip_label = tk.Label(self.ip_frame, text="IP(s) / Host(s):")
        # Entry for IP or IP list
        self.ip_entry = JaideEntry(self.ip_frame)
        # Button to open file of list of IPs
        self.ip_button = tk.Button(self.ip_frame, text="Select File", command=lambda: self.open_file(self.ip_entry), takefocus=0)
        # compiled regex for testing IP address(es)
        self.ip_test = re.compile(r'^(((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))(,|(,\ ))?)+$')

        #### CONNECTION TIMEOUT
        self.timeout_label = tk.Label(self.ip_frame, text="Timeout:")
        self.timeout_entry = JaideEntry(self.ip_frame, instance_type=int, contents=300)

        ##### USERNAME
        # label for Username
        self.username_label = tk.Label(self.creds_frame, text="Username: ")
        # Entry widget for username
        self.username_entry = JaideEntry(self.creds_frame)
        
        ##### PASSWORD
        # label for Password
        self.password_label = tk.Label(self.creds_frame, text="Password: ")
        # Entry widget for username
        self.password_entry = JaideEntry(self.creds_frame, show="*")

        ### WRITE TO FILE
        # Entry for Write to File
        self.wtf_entry = JaideEntry(self.wtf_frame)
        # Write to File button
        self.wtf_button = tk.Button(self.wtf_frame, text="Select File", command=self.open_wtf, takefocus=0)
        # Write to file checkbox
        self.wtf_checkbox = JaideCheckbox(self.wtf_frame, text="Write to file", command=self.check_wtf, takefocus=0)

        # Help label sits next in the target device section
        self.help_value = tk.StringVar("")
        self.help_label = tk.Label(self.help_frame, textvariable=self.help_value, justify="left", anchor="nw", wraplength=750)

        ### OPTIONS
        # stores which option from options_list is selected
        self.option_value = tk.StringVar()
        # sets defaulted option to first one
        self.option_value.set(self.options_list[0])
        # Actual dropdown list widget. Uses PMW because tk base doesn't allow an action to be bound to an option_menu.
        self.option_menu = Pmw.OptionMenu(self.options_frame, command=self.opt_select, menubutton_textvariable=self.option_value, items=self.options_list)
        # Prevents option_menu from taking focus while tabbing
        self.option_menu.component('menubutton').config(takefocus=0)
        # Entry field for argument modifier.
        self.option_entry = JaideEntry(self.options_frame)

        ### SCP OPTIONS
        # variable to track what is chosen in the scp_direction_menu menu
        self.scp_direction_value = tk.StringVar()
        self.scp_direction_value.set("Push")
        # scp direction menu to choose push or pull
        self.scp_direction_menu = tk.OptionMenu(self.options_frame, self.scp_direction_value, 'Push', 'Pull')
        # File load button for SCP source
        self.scp_source_button = tk.Button(self.options_frame, text="Local Source", command=lambda: self.open_file(self.option_entry), takefocus=0)
        # second file load button for SCPing
        self.scp_destination_button = tk.Button(self.options_frame, text="Local Destination", command=lambda: self.open_file(self.scp_destination_entry), takefocus=0)
        # second entry field for SCPing
        self.scp_destination_entry = JaideEntry(self.options_frame)
        
        # set_list_button is used to find a file containing a list of set commands.
        self.set_list_button = tk.Button(self.options_frame, text="Select File", command=lambda: self.open_file(self.option_entry), takefocus=0)
        
        ### COMMIT CHECK, COMMIT CONFIRMED, and COMMIT BLANK options.
        # commit check checkbox
        self.commit_check_button = JaideCheckbox(self.options_frame, text="Commit Check Only", command=lambda: self.commit_option_update('check'), takefocus=0)
        # commit confirmed checkbox and minutes entry label / field. 
        self.commit_confirmed_button = JaideCheckbox(self.options_frame, text="Commit Confirmed", command=lambda: self.commit_option_update('confirmed'), takefocus=0)
        self.commit_confirmed_min_label = tk.Label(self.options_frame, text="Minutes: ", takefocus=0) 
        # The commit confirmed minutes selector, which is a scale between 1 and 60. 
        self.commit_confirmed_min_entry = tk.Scale(self.options_frame, from_=1, to=60, orient='horizontal', takefocus=0)
        # Commit blank option
        self.commit_blank = JaideCheckbox(self.options_frame, text="Blank Commit", command=lambda: self.commit_option_update('blank'), takefocus=0)
        # These are used to keep rows 1 and 2 of options_frame from being empty and thus hidden
        self.spacer_label = tk.Label(self.options_frame, takefocus=0)

        ### Buttons
        self.go_button = tk.Button(self.buttons_frame, command=lambda: self.go(None), text="Run Script", takefocus=0)
        self.stop_button = tk.Button(self.buttons_frame, text="Stop Script", command=self.stop_script, state="disabled", takefocus=0)
        self.clear_button = tk.Button(self.buttons_frame, command=lambda: self.clear_output(None), text="Clear Output", state="disabled", takefocus=0)
        self.save_button = tk.Button(self.buttons_frame, command=self.save_output, text="Save Output", state="disabled", takefocus=0)
        self.toggle_frames_button = tk.Button(self.buttons_frame, command=self.toggle_frames, text="Toggle Options", takefocus=0)

        ### SCRIPT OUTPUT AREA
        self.output_area = tk.Text(self.output_frame, wrap=tk.NONE)
        self.xscrollbar = AutoScrollbar(self.output_frame, command=self.output_area.xview, orient=tk.HORIZONTAL, takefocus=0)
        self.yscrollbar = AutoScrollbar(self.output_frame, command=self.output_area.yview, takefocus=0)
        self.output_area.config(yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set, takefocus=0)

        # Separators
        self.sep1 = ttk.Separator(self.ip_cred_frame)
        self.sep2 = ttk.Separator(self)
        self.sep3 = ttk.Separator(self)
        self.sep4 = ttk.Separator(self)
        self.sep5 = ttk.Separator(self)

        #############################################
        # Put the objects we've created on the grid #
        # for the user to see.                      #
        #############################################
        ### INITIALIZE THE LAYOUT
        self.show_frames()
        self.rowconfigure(9, weight=1)
        self.columnconfigure(0, weight=1)
        self.output_frame.rowconfigure(0, weight=1)
        self.output_frame.columnconfigure(0, weight=1)

        ### GRIDDING FOR ALL WIDGETS VISIBLE AT FIRST LOAD.
        # Section 0 - Target Device(s) - ip_frame
        self.ip_frame.grid(column=0, row=0, sticky="NW")
        self.ip_label.grid(column=0, row=0, sticky="NW")
        self.ip_entry.grid(column=1, row=0, sticky="NW")
        self.ip_button.grid(column=2, row=0, sticky="NW")
        self.timeout_label.grid(column=0, row=1, sticky="NW")
        self.timeout_entry.grid(column=1, row=1, sticky="NW")
        self.sep1.grid(column=1, row=0, sticky="NS", padx=(18, 18))

        # Section 1 - Authentication - creds_frame
        self.creds_frame.grid(column=2, row=0, sticky="NW")
        self.username_label.grid(column=0, row=0, sticky="NW")
        self.username_entry.grid(column=1, row=0, sticky="NW")
        self.password_label.grid(column=0, row=1, sticky="NW")
        self.password_entry.grid(column=1, row=1, sticky="NW")

        # This is the help label in the frame below the options frame.
        self.help_label.grid(column=0, row=0, sticky="NWES")
        
        # Section 2 - Write to File - wtf_frame
        self.wtf_checkbox.grid(column=0, row=0, sticky="NSW")
                
        # Section 3 - Command Options - options_frame
        self.option_menu.grid(column=0, row=0, sticky="EW")
        self.spacer_label.grid(column=0, row=1, sticky="NW")
        
        # Section 4 - Action Buttons - buttons_frame
        self.go_button.grid(column=0, row=0, sticky="NW", padx=2)
        self.stop_button.grid(column=1, row=0, sticky="NW", padx=2)
        self.clear_button.grid(column=2, row=0, sticky="NW", padx=2)
        self.save_button.grid(column=3, row=0, sticky="NW", padx=2)
        self.toggle_frames_button.grid(column=4, row=0, sticky="NW", padx=2)

        # Section 5 - Output Area - output_frame
        self.output_area.grid(column=0, row=0, sticky="SWNE")
        self.output_area.columnconfigure(0, weight=100)
        self.xscrollbar.grid(column=0, row=1, sticky="SWNE")
        self.yscrollbar.grid(column=1, row=0, sticky="SWNE")
        
        # Set the window to a given size. This prevents autoscrollbar 'fluttering' behaviour, 
        # and stabilizes how the Toggle Output button behaves.
        self.geometry('800x800')

        # Sets the tab order correctly
        self.ip_frame.lift()
        self.creds_frame.lift()
        self.wtf_frame.lift()
        self.options_frame.lift()
        
        # Run the opt_select method to ensure the proper fields are shown. 
        self.opt_select(None)
        

    def go(self, event):
        """ Purpose: This function is called when the user clicks on the 'Run Script' button. It inserts output 
                     letting the user know the script has started, spawns a subprocess running a WorkerThread instance.
                     It also builds and presents the user with the jaide.py commmand,  and modifies the different buttons
                      availability, now that the script has started.

            Parameters:
                event - Tkinter.event object - Any command that tkinter binds a keyboard shortcut to will receive the
                        argument event. It is a description of the keyboard shortcut that generated the event. 
        """
        # This checks the input validation and only continues if we return true. 
        if self.input_validation():
            # puts cursor at end of text field
            self.output_area.mark_set(tk.INSERT, tk.END)
            self.write_to_output_area("\n****** Process Starting ******\n")

            # Gets username/password/ip from appropriate StringVars
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()
            ip = self.ip_entry.get()
            timeout = self.timeout_entry.get()
            if self.wtf_checkbox.get() == 1:  # test if write to file is checked.
                wtf = self.wtf_entry.get() 
            else:
                wtf = ""

            # Looks up the selected option from dropdown against the conversion dictionary to get the right Jaide function to call
            function = self.option_conversion[self.option_value.get()]

            # start building the jaide command to let the user know how they can use the CLI tool to do the same thing.
            jaide_command = 'python jaide.py -u ' + username + ' -i ' + ip
            options = {
                    "Operational Command(s)" : ' -c ',
                    "Interface Errors" : ' -e ',
                    "Health Check" : ' --health ',
                    "Device Info" : ' --info ',
                    "Set Command(s)" : ' -s ',
                    "SCP Files" : ' --scp ',
                    "Shell Command(s)" : ' --shell '
                }
            jaide_command += options[self.option_value.get()]  # add the argument flag for the item they've chosen in the optionMenu

            # Logic to pass appropriate variables to WorkerThread for subsequent Jaide call
            # SCP passes a dictionary which WorkerThread has logic to pull from. Done this way because the args in Jaide.copy_file are poorly ordered for handling otherwise
            if self.option_value.get() == "SCP Files":
                argsToPass = {
                        "scp_source" : self.option_entry.get(),
                        "scp_dest" : self.scp_destination_entry.get(),
                        "direction" : self.scp_direction_value.get(),
                        "write" : True,
                        "callback" : None,
                        "multi" : True
                    }
                jaide_command += self.scp_direction_value.get() + ' ' + self.option_entry.get() + ' ' + self.scp_destination_entry.get()
            # List of args that can be easily unpacked by jaide.do_netconf
            elif self.option_value.get() == 'Set Command(s)':
                jaide_command += '\"' + self.option_entry.get() + '\"'
                if self.commit_confirmed_button.get():  # Commit Confirmed
                    jaide_command += ' --confirmed ' + str(self.commit_confirmed_min_entry.get())
                    argsToPass = [self.option_entry.get(), False, True, self.commit_confirmed_min_entry.get(), False]
                elif self.commit_check_button.get():  # Commit Check
                    jaide_command += ' --check '
                    argsToPass = [self.option_entry.get(), True, True, False, False]
                elif self.commit_blank.get():  # Commit Blank. 
                    jaide_command = jaide_command.split('-s')[0] + '--blank '
                    argsToPass = [self.option_entry.get(), False, True, False, True]
                else:  # Neither confirm, check or blank, just regular commit. 
                    argsToPass = [self.option_entry.get(), False, True, False, False]
            
            elif self.option_value.get() == 'Shell Command(s)':
                jaide_command += '\"' + self.option_entry.get() + '\"'
                argsToPass = [self.option_entry.get().strip(), True, timeout]

            # The only other option left in yes_options is "Operational Command(s)". 
            elif self.option_value.get() in self.yes_options:
                jaide_command += '\"' + self.option_entry.get() + '\"'
                argsToPass = [self.option_entry.get().strip(), False, timeout]
            
            # If the function does not need any additional arguments
            elif self.option_value.get() in self.no_options:            
                argsToPass = None
            
            # If we could not figure out what we're doing, error out instead of making bogus calls to doJaide()
            # This really should never be a possibility, as long as we've coded the other parts of this if statement to catch everything.
            else:
                self.write_to_output_area("We've hit an error parsing the command you entered. Our code must be terrible.")
                return

            # print the CLI command to the user so they know how about jaide.py
            self.write_to_output_area('The following command can be used to do this same thing on the command line:\n%s' % jaide_command)
            if "|" in jaide_command:
                self.write_to_output_area('Your CLI command will have pipes, \'|\', be wary of your environment and necessary escaping.\nCheck the working-with-pipes.html file in the examples folder for more information.')
            self.write_to_output_area('\n')  # add an extra line to separate the CLI suggestion from the rest of the output. 
            
            # Create the WorkerThread class to run the Jaide functions.
            self.thread = WorkerThread(
                    argsToPass=argsToPass,
                    timeout=timeout,
                    command=function,
                    stdout_queue=self.stdout_queue,
                    ip=ip,
                    username=username,
                    password=password,
                    write_to_file=wtf
                )
            self.thread.daemon = True
            self.thread.start()

            # Change the state of the buttons now that the script is running, so the user can save the output, kill the script, etc. 
            self.go_button.configure(state="disabled")
            self.clear_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.save_button.configure(state="disabled")
            self.get_output()


    def get_output(self):
        """ Purpose: This function listens to the sub process generated by the 'Run Script' button, and 
                     dumps the output to the output_area using the function write_to_output_area. If the process
                     is no longer alive, it changes the activation of buttons, and lets the user know that the script 
                     is done. 
        """
        try:  # pull from the stdout_queue, and write it to the output_area
            self.write_to_output_area(self.stdout_queue.get_nowait())
        except Queue.Empty:  # Nothing in the queue, but the thread could be still alive, try again next time around.
            pass
        if not self.thread.isAlive():  # The WorkerThread subprocess has completed, and we need to wrap up.
            while not self.stdout_queue.empty():
                self.write_to_output_area(self.stdout_queue.get_nowait())
            self.go_button.configure(state="normal")
            self.clear_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.save_button.configure(state="normal")
            self.write_to_output_area("\n****** Process Completed ******\n")
            self.thread.join()
            return
        self.after(100, self.get_output)  # recursively call this function every 100ms, writing any new output. 


    def input_validation(self):
        """ Purpose: This function is used to validate the inputs of the user when they press the 'Run Script' button.
                     It will return a boolean with True for passing the checks, and False if we failed the validation.
        """
        # IP address entry must be a valied ipv4 address if we're running against a single ip
        if not re.match(self.ip_test, self.ip_entry.get().strip()) and not os.path.isfile(self.ip_entry.get().strip()):
            tkMessageBox.showinfo("IP Entry", "Either an invalid IP address was entered, an invalid comma separated list of IPs, or the IP Address list file not found.")
        # Making sure the user typed something into the IP field. 
        elif self.ip_entry.get() == "":  
            tkMessageBox.showinfo("IP Entry", "Please enter an IP address or IP address list file.")
        # Ensure there is a value typed into the username and password fields.
        elif self.username_entry.get() == "" or self.password_entry.get() == "":
            tkMessageBox.showinfo("Credentials", "Please enter a username and password.")
        # If the write to file box is checked, they must have something typed in for an output file. 
        elif self.wtf_entry.get() == "" and self.wtf_checkbox.get(): 
            tkMessageBox.showinfo("Write to File", "When writing to a file, a filename must be specified.")
        # Ensure that if an option is chosen that requires extra input that they have something in the entry widget. 
        elif self.option_value.get() in self.yes_options and self.option_entry.get() == "" and self.commit_blank.get() == 0:
            tkMessageBox.showinfo("Option Input", "You chose an option that requires extra input, and didn't specify any additional information. " +
                "For example, when selecting \"Operational Command(s)\", a command string must be typed into the entry box.")
        else:  
            # Make sure the timeout value is a number. 
            try:
                isinstance(self.timeout_entry.get(), int)
            except ValueError:
                tkMessageBox.showinfo("Timeout", "A timeout value must be an integer, in seconds.")
            else:  # If all else fails, they passed.
                return True


    def show_about(self):
        """ Purpose: This will show the about text for the application.
        """
        aboutInfo = tk.Toplevel()
        aboutInfoLabel = tk.Label(aboutInfo, text="The Jaide GUI Application is a GUI wrapper for the jaide.py script.\n\r"
            "Version 0.9.0\n\rContributors: Geoff Rhodes and Nathan Printz\n\rMore information about Jaide and the Jaide"
            " GUI can be found at https://github.com/nprintz/jaide", padx=50, pady=50)
        aboutInfoLabel.pack()


    def show_help(self):
        """ Purpose: This is called when the user selects the 'Help Text' menubar option. It opens the README.html file
                     in their default browser. If the file doesn't exist it opens the github readme page instead.
        """
        # Grab the directory where the script is running.
        readme = module_path()
        # Determine our OS, attach the README.html file to the path, and open that file.
        if sys.platform.startswith('darwin'):
            readme += "/README.html"
            if os.path.isfile(readme):
                subprocess.call(('open', readme))
            else:
                try:
                    webbrowser.open('https://github.com/nprintz/jaide')
                except webbrowser.Error:
                    pass
        elif os.name == 'nt':
            readme += "\\README.html"
            if os.path.isfile(readme):
                os.startfile(readme)  # this works on windows, not sure why pylint shows an error. 
            else: 
                try:
                    webbrowser.open('https://github.com/nprintz/jaide')
                except webbrowser.Error:
                    pass
        elif os.name == 'posix':
            readme += "/README.html"
            if os.path.isfile(readme):
                subprocess.call(('xdg-open', readme))
            else: 
                try:
                    webbrowser.open('https://github.com/nprintz/jaide')
                except webbrowser.Error:
                    pass


    def show_examples(self):
        """ Purpose: This method opens the example folder for the user, or open the github page for the example folder. 
        """
        # Grab the directory that the script is running from. 
        examples = module_path()
        # Determin our OS, attach the README.html file to the path, and open that file.
        if sys.platform.startswith('darwin'):
            examples += "/examples/"
            if os.path.isdir(examples):
                subprocess.call(('open', examples))
            else:
                try:
                    webbrowser.open('https://github.com/nprintz/jaide/examples')
                except webbrowser.Error:
                    pass
        elif os.name == 'nt':
            examples += "\\examples\\"
            if os.path.isdir(examples):
                os.startfile(examples)  # this works on windows, not sure why pylint shows an error. 
            else: 
                try:
                    webbrowser.open('https://github.com/nprintz/jaide/examples')
                except webbrowser.Error:
                    pass
        elif os.name == 'posix':
            examples += "/examples/"
            if os.path.isdir(examples):
                subprocess.call(('xdg-open', examples))
            else: 
                try:
                    webbrowser.open('https://github.com/nprintz/jaide/examples')
                except webbrowser.Error:
                    pass


    def write_to_output_area(self, output):
        """ Purpose: This method will insert the passed string 'output' at the end of the output_area, and will 
                     also scroll the viewable area to the bottom.
            Passed Arguments:
                output  -   String of the output to dump to the output_area
        """
        if output is not None:
            if isinstance(output, basestring):
                if output[-1:] is not "\n":
                    output = output + "\n"
                # SCP was putting None to the output queue and this throws an error with insert
                self.output_area.insert(tk.END, output)
                self.output_area.see(tk.END)


    def save_template(self, event):
        """ Purpose: asks for a file name and writes all variable information to it.
                     Passwords are obfuscated with Base64 encoding, but this is
                     by no means considered secure.

            Parameters:
                event - Tkinter.event object - Any command that tkinter binds a keyboard shortcut to will receive the
                        argument event. It is a description of the keyboard shortcut that generated the event. 
         """
        returnFile = tkFileDialog.asksaveasfilename()
        if returnFile:
            try:
                output_file = open(returnFile, 'wb')
            except IOError as e:
                self.write_to_output_area("Couldn't open file to save. Error: \n" + str(e))
            else:
                # Write every field to the template file. 
                output_file.write("IP:~:" + self.ip_entry.get() + "\n")
                output_file.write("Timeout:~:" + str(self.timeout_entry.get()) + "\n")
                output_file.write("Username:~:" + self.username_entry.get() + "\n")
                output_file.write("Password:~:" + base64.b64encode(self.password_entry.get()) + "\n")
                output_file.write("WriteToFileBool:~:" + str(self.wtf_checkbox.get()) + "\n")
                output_file.write("WriteToFileLoc:~:" + self.wtf_entry.get() + "\n")
                output_file.write("Option:~:" + self.option_value.get() + "\n")
                output_file.write("FirstArgument:~:" + self.option_entry.get() + "\n")
                output_file.write("SCPDest:~:" + self.scp_destination_entry.get() + "\n")
                output_file.write("SCPDirection:~:" + self.scp_direction_value.get() + "\n")
                output_file.write("CommitCheck:~:" + str(self.commit_check_button.get()) + "\n")
                output_file.write("CommitConfirmed:~:" + str(self.commit_confirmed_button.get()) + "\n")
                output_file.write("CommitConfirmedMin:~:" + str(self.commit_confirmed_min_entry.get()) + "\n")
                output_file.write("CommitBlank:~:" + str(self.commit_blank.get()) + "\n")
                output_file.close()


    def open_template(self, event):
        """ Purpose: Loads variable info from file and populates it in to GUI 

            Parameters:
                event - Tkinter.event object - Any command that tkinter binds a keyboard shortcut to will receive the
                        argument event. It is a description of the keyboard shortcut that generated the event. 
        """
        returnFile = tkFileDialog.askopenfilename()
        if returnFile:
            try:
                input_file = open(returnFile, "rb")
            except IOError as e:
                self.write_to_output_area("Couldn't open file to import. Error: \n" + str(e))
            else:
                input_vars = input_file.readlines()
                input_file.close()
                # Read the template file and set the fields accordingly. 
                self.ip_entry.set(input_vars[0].split(':~:')[1].rstrip())
                self.timeout_entry.set(input_vars[1].split(':~:')[1].rstrip())
                self.username_entry.set(input_vars[2].split(':~:')[1].rstrip())
                self.password_entry.set(base64.b64decode(input_vars[3].split(':~:')[1].rstrip()))
                self.wtf_checkbox.set(input_vars[4].split(':~:')[1].rstrip())
                self.wtf_entry.set(input_vars[5].split(':~:')[1].rstrip())
                self.option_value.set(input_vars[6].split(':~:')[1].rstrip())
                # Once we've set the option menu value, we need to display any appropriate field before continuing
                self.opt_select(None)
                # Now that the menu option is set, the other fields will be visible to populate.
                self.option_entry.set(input_vars[7].split(':~:')[1].rstrip())
                self.scp_destination_entry.set(input_vars[8].split(':~:')[1].rstrip())
                self.scp_direction_value.set(input_vars[9].split(':~:')[1].rstrip())
                self.commit_check_button.set(input_vars[10].split(':~:')[1].rstrip())
                self.commit_confirmed_button.set(input_vars[11].split(':~:')[1].rstrip())
                self.commit_confirmed_min_entry.set(input_vars[12].split(':~:')[1].rstrip())
                self.commit_blank.set(input_vars[13].split(':~:')[1].rstrip())
                # check wtf, commit check, and commit confirmed to see if they are checked. 
                self.check_wtf()
                self.commit_option_update('confirmed')
                self.commit_option_update('check')
                self.commit_option_update('blank')


    def stop_script(self):
        """ Purpose: Called to kill the subprocess 'jaide' which is actually running the jaide.py script. 
                     This is called when the user clicks on the Stop Script button.
        """
        self.thread.kill_proc()
        self.write_to_output_area("\n****** Attempting to stop process ******\n")



    def opt_select(self, none):
        """ Purpose: This is used to show and hide options as different items are selected from the drop down accordingly.
        """
        # First thing we do is forget all placement and deselect options, then we'll update according to what they chose afterwards.
        self.commit_check_button.grid_forget()
        self.commit_check_button.deselect()
        self.commit_confirmed_button.deselect()
        self.commit_confirmed_button.grid_forget()
        self.commit_confirmed_min_label.grid_forget()
        self.commit_confirmed_min_entry.grid_forget()
        self.commit_blank.grid_forget()
        self.option_entry.grid_forget()
        self.set_list_button.grid_forget()
        self.scp_source_button.grid_forget()
        self.scp_destination_entry.grid_forget()
        self.scp_destination_button.grid_forget()
        self.scp_direction_menu.grid_forget()    
        self.spacer_label.grid_forget()

        if self.option_value.get() == "------":
            self.option_value.set("Device Info")

        # SCP
        if self.option_value.get() == "SCP Files":
            self.scp_direction_menu.grid(column=1, columnspan=2, row=0, sticky="NW")
            self.option_entry.grid(column=0, row=1, sticky="NW")
            self.scp_source_button.grid(column=1, row=1, sticky="NW", padx=2)
            self.scp_destination_entry.grid(column=2, row=1, sticky="NW")
            self.scp_destination_button.grid(column=3, row=1, sticky="NW", padx=2)

        # Any option that requires a single text arg
        elif self.option_value.get() in self.yes_options:
            self.option_entry.grid(column=1, columnspan=2, row=0, sticky="NW")
            
            # If we are getting a list of set command, show file open button and commit check / confirmed boxes
            if self.option_value.get() == "Set Command(s)":
                self.set_list_button.grid(column=3, row=0, sticky="NW", padx=2)
                self.commit_check_button.grid(column=0, row=1, sticky="NW")
                self.commit_confirmed_button.grid(column=2, row=1, sticky="NW")
                self.commit_blank.grid(column=1, row=1, sticky="NW")
            else:
                self.spacer_label.grid(column=1, columnspan=2, row=1, sticky="NW")

            if self.option_value.get() == "Operational Command(s)":
                self.set_list_button.grid(column=3, row=0, sticky="NW", padx=2)
        else:
            # No option
            self.spacer_label.grid(column=1, columnspan=2, row=1, sticky="NW")

        # Update the help text for the new command
        self.help_value.set(self.help_conversion[self.option_value.get()])
        time.sleep(.05)  # sleep needed to avoid artifacting when updating the frames
        # Update the UI after we've made our changes
        self.update()


    def open_file(self, entry_object):
        """ Purpose: This method is used to prompt the user to find a file on their local machine that already exists. Once
                     they've selected a file, we will put the full filepath to that file in the text entry object that was 
                     passed to this method. If the user does not specify a file (ie. presses the 'cancel' button on the 
                     dialog box), then we will not update the entry field, we do nothing. 
            Parameters:
                entry_object - Tkinter.Entry object - This is the actual displayed Tkinter Entry object where the filepath 
                               that the user specifies will be dumped to. 
        """
        # ask the user for a local file, and if they give us one, replace the passed entry field. 
        returnFile = tkFileDialog.askopenfilename()
        if returnFile:
            # Deletes whatever is in the field currently
            entry_object.delete(0, tk.END)
            # Puts the selected file (w/ full path) in to field
            entry_object.insert(0, returnFile)
    

    def open_wtf(self):
        """ Purpose: This will delete whatever is in the wtf_entry field, and prompt the user with a find file dialog box.
                     Once they've found the file, it will insert that filepath into wtf_entry. This function is only called 
                     when the 'Select File' button next to wtf_entry is clicked. 
        """
        # Retrieve a filename from the user
        returnFile = tkFileDialog.asksaveasfilename()
        if returnFile:
            # removes everything in wtf_entry
            self.wtf_entry.delete(0, tk.END)
            # puts full path of selected file to save as in wtf_entry
            self.wtf_entry.insert(0, returnFile)


    def check_wtf(self):
        """ Purpose: This function is called whenever the user clicks on the checkbox for writing output to a file. It will take the 
                     appropriate action based on whether the box was checked previously or not. If it is now checked, it 
                     will add the wtf_entry and wtf_button options for specifying a file to write the output to. If it is 
                     now unchecked, it will remove these two objects.                      
        """
        # if WTF checkbox is checked,  enable the Entry and file load button
        if self.wtf_checkbox.get() == 1:
            self.wtf_entry.grid(column=1, row=0)
            self.wtf_button.grid(column=2, row=0, sticky="NW", padx=2)
        # if WTF checkbox is not checked,  re-disable the entry options
        if self.wtf_checkbox.get() == 0:
            self.wtf_entry.grid_forget()
            self.wtf_button.grid_forget()


    def commit_option_update(self, check_type):
        """ Purpose: This function is called when any of the commit option check boxes are clicked. Depending on which one we click, we 
                     deselect the other two, and forget or create the grid for the commit confirmed minutes entry as necessary. 
            Parameters:
                check_type  -  string  -  a string identifier stating which commit option is being clicked. We are expecting one of three 
                                          options: 'blank', 'check', or 'confirmed'.
        """
        if check_type == 'blank' and self.commit_blank.get():
            self.commit_confirmed_button.deselect()
            self.commit_check_button.deselect()
            self.commit_confirmed_min_entry.grid_forget()
            self.commit_confirmed_min_label.grid_forget()
        elif check_type == 'check' and self.commit_check_button.get():
            self.commit_confirmed_button.deselect()
            self.commit_blank.deselect()
            self.commit_confirmed_min_entry.grid_forget()
            self.commit_confirmed_min_label.grid_forget()
        elif check_type == 'confirmed' and self.commit_confirmed_button.get():
            self.commit_check_button.deselect()
            self.commit_blank.deselect()
            self.commit_confirmed_min_label.grid(column=3, row=1, sticky="NW")
            self.commit_confirmed_min_entry.grid(column=4, row=1, sticky="NW")
        elif check_type == 'confirmed' and not self.commit_confirmed_button.get():
            self.commit_confirmed_min_entry.grid_forget()
            self.commit_confirmed_min_label.grid_forget()


    def clear_output(self, event):
        """ Purpose: This function is called by the 'clear output' button and is used to remove all text from the output window. 

            Parameters:
                event - Tkinter.event object - Any command that tkinter binds a keyboard shortcut to will receive the
                        argument event. It is a description of the keyboard shortcut that generated the event. 
        """
        self.output_area.delete(1.0, tk.END)


    def save_output(self):
        """ Purpose: This function is called by the 'save output' button and is used to open a save file dialog box, and write
                     the text within the output_area window to that file. """
        returnFile = tkFileDialog.asksaveasfilename()
        # If no file is chosen, do not try to open it.
        if returnFile is not "":
            outFile = open(returnFile, 'w+b')  # 'w' will open for overwriting, 'b' is for windows compatibility
            outFile.write(self.output_area.get(1.0, tk.END))
            outFile.close()


    def quit(self, event):
        """ Purpose: Quit the application, called on selecting File > Quit, or by pressing Ctrl-Q. 

            Parameters:
                event - Tkinter.event object - Any command that tkinter binds a keyboard shortcut to will receive the
                        argument event. It is a description of the keyboard shortcut that generated the event. 
        """
        sys.exit(0)


    def clear_fields(self, event):
        """ Purpose: Clear all input fields. Called by hitting Ctrl-C or clicking the appropriate menu option in the file menu.

            Parameters:
                event - Tkinter.event object - Any command that tkinter binds a keyboard shortcut to will receive the
                        argument event. It is a description of the keyboard shortcut that generated the event. 'None' can be passed
                        for method calls outside of a keyboard shortcut. 
        """
        self.ip_entry.delete(0, tk.END)
        self.timeout_entry.delete(0, tk.END)
        self.timeout_entry.insert(0, '300')
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.wtf_entry.delete(0, tk.END)
        self.wtf_checkbox.deselect()
        self.option_entry.delete(0, tk.END)
        self.option_entry.delete(0, tk.END)
        self.scp_destination_entry.delete(0, tk.END)
        self.commit_check_button.deselect()
        self.commit_confirmed_button.deselect()
        self.commit_blank.deselect()


    def show_frames(self):
        """ Purpose: This function grids all frames and separators. It is called by the Toggle Options button, and used by
                     __init__() to create the frames on starting the program. 
        """

        self.ip_cred_frame.grid(row=0, column=0, sticky="NW", padx=(25,25), pady=(25, 0))
        
        self.sep2.grid(row=1, column=0, sticky="WE", pady=8, padx=8)

        self.wtf_frame.grid(row=2, column=0, sticky="NW", padx=(25, 0))
        self.sep3.grid(row=3, column=0, sticky="WE", pady=8, padx=8)
        
        self.options_frame.grid(row=4, column=0, sticky="NW", padx=(25, 0))

        self.sep4.grid(row=5, column=0, sticky="WE", pady=12, padx=12)

        self.help_frame.grid(row=6, column=0, sticky="NW", padx=(25, 0))

        self.sep5.grid(row=7, column=0, sticky="WE", pady=12, padx=12)
        
        self.buttons_frame.grid(row=8, column=0, sticky="NW", padx=(25, 25), pady=(0, 10))
        self.output_frame.grid(row=9, column=0, padx=(25, 25), sticky="SWNE", pady=(0, 25))
        
        self.update()


    def toggle_frames(self):
        """ This function is called by toggle_frames_button to toggle whether non-output frames are shown. """
        if self.frames_shown:
            self.ip_cred_frame.grid_forget()
            self.wtf_frame.grid_forget()
            #self.options_frame.grid_forget()
            self.help_frame.grid_forget()

            self.sep2.grid_forget()
            self.sep3.grid_forget()
            self.sep4.grid_forget()
            #self.sep5.grid_forget()

            self.update()
            self.frames_shown = False
        else:
            self.show_frames()
            self.frames_shown = True


if __name__ == "__main__":
    # freeze support provides support for compiling to a single executable.
    mp.freeze_support()
    gui = JaideGUI(None)
    gui.mainloop()
