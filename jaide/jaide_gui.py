""" The GUI wrapper for the jaide_cli.py CLI script.

This python file is used to spawn the GUI that wraps around jaide.py,
providing ease of use for those that don't want to use the command line.
This Class is part of the jaide/jgui project.
It is free software for use in manipulating junos devices. More information
can be found at the github page found here:

   https://github.com/NetworkAutomation/jaide
"""
try:
    # ## Tkinter related imports.
    import Tkinter as tk  # Tkinter is the underlying gui framework.
    import tkFileDialog
    import tkMessageBox  # to prompt users during input validation errors
    import ttk  # Used for separators between frames of the UI.
    # Pmw is the extended menuwidget option giving us the ability
    # to call a function when a option is chosen from the menu.
    import Pmw
    # ## Processing and queuing
    import subprocess  # Used for opening help file with the browser.
    import Queue
    # In terms of JGUI, we use multiprocessing to enable freeze_support.
    # The worker_thread subpackage uses multiprocessing further to run
    # concurrent instances of the Jaide script.
    import multiprocessing as mp
    # ## Basic functions and manipulation.
    import webbrowser
    import re
    import os
    import sys
    import base64
    import time
    # ## The following imports are modules that we have written.
    import jaide_cli
    # the jgui_widgets module extends Tkinter widgets for use within Jaide GUI
    from jgui.jgui_widgets import JaideEntry, JaideCheckbox
    from jgui.jgui_widgets import AutoScrollbar, JaideRadiobutton
    from jgui.worker_thread import WorkerThread
    from jgui.module_locator import module_path
except ImportError as e:
    print "Failed to import one or more packages! Non-standard packages for the GUI include:\nPMW\t\thttp://pmw.sourceforge.net/\n\nScript Error:\n"
    raise e


# TODO: make Script output non-editable, but still selectable for copying.  - Doesn't seem feasible without completely re-writing textArea widget.
# TODO: add headers to the sections of the GUI / add coloring or styling.  - Attempted, couldn't get menuoption to work, or checkboxes on mac.
# TODO: make entry fields fill their given space on the x-axis to give more space for filepaths?
# TODO: check and make sure writing to multiple files works on windows and compiled versions.
class JaideGUI(tk.Tk):

    """ The GUI wrapper for the jaide_cli.py CLI tool.

    The JaideGUI class inherits the properties of the Tkinter.Tk class. This
    class encapsulates the entire methodology for creating the visual
    representation seen by the user. Some functionality is enhanced with the
    use of other classes that are imported and used, including WorkerThread
    (for running the jaide.py script and handling output gathering) and
    AutoScrollbar (for putting scrollbars on the output_area text entry widget)
    """

    def __init__(self, parent):
        """ Purpose: Initializes and shows the GUI. """
        tk.Tk.__init__(self, parent)
        self.parent = parent

        self.grid()
        self.wm_title("Jaide GUI")
        self.focus_force()
        self.defaults_file = os.path.join(module_path(), "defaults.ini")

        # ## Argument and option lists for user input
        # arguments that require extra input
        self.yes_options = ["Operational Command(s)", "Set Command(s)",
                            "Shell Command(s)", "SCP Files", "Diff Config"]
        # arguments that don't require extra input
        self.no_options = ["Interface Errors", "Health Check", "Device Info"]
        # List of argument options
        self.options_list = ["Diff Config", "Operational Command(s)",
                             "Set Command(s)", "Shell Command(s)", "SCP Files",
                             "------", "Device Info", "Health Check",
                             "Interface Errors"]

        # Maps optionMenu choice to jaide_cli function.
        self.option_conversion = {
            "Diff Config": jaide_cli.diff_config,
            "Device Info": jaide_cli.dev_info,
            "Health Check": jaide_cli.health_check,
            "Interface Errors": jaide_cli.int_errors,
            "Operational Command(s)": jaide_cli.multi_cmd,
            "SCP Files": jaide_cli.copy_file,
            "Set Command(s)": jaide_cli.commit,
            "Shell Command(s)": jaide_cli.multi_cmd
        }
        # Maps optionMenu choice to help text.
        self.help_conversion = {
            "Device Info": "Quick Help: Device Info pulls some baseline information from the device(s), including " +
                        "Hostname, Model, Junos Version, and Chassis Serial Number.",
            "Diff Config": "Quick Help: Compare the configuration between two devices. Specify the second IP/hostname," +
                        " and choose whether to do set mode or stanza mode.",
            "Health Check": "Quick Help: Health Check runs multiple commands to get routing-engine CPU/memory info, " +
                        "busy processes, temperatures, and alarms. The output will likely show the mgd process using " +
                        "high CPU, this is normal due to the execution of the script logging in and running the commands.",
            "Interface Errors": "Quick Help: Interface Errors will tell you of any input or output errors on all interfaces.",
            "Operational Command(s)": "Quick Help: Run one or more operational command(s) against the device(s). This can " +
                        "be any non-interactive command(s) that can be run from operational mode. This includes show, " +
                        "request, traceroute, op scripts, etc.",
            "SCP Files": "Quick Help: SCP file(s) or folder(s) to or from one or more devices. Specify a source and destination " +
                        "file or folder. If Pulling, the source is the remote file/folder, and the destination is the local " +
                        "folder you are putting them. If Pushing, the source is the local file/folder, and the destination would" +
                        " the folder to put them on the remote device. Note, the '~' home directory link can not be used!",
            "Set Command(s)": "Quick Help: A single or multiple set commands that will be sent and committed to the device(s). " +
                        "There are additional optional commit modifiers, which can be used to do several different things. " +
                        "Much more information can be found in the help files.",
            "Shell Command(s)": "Quick Help: Send one or more shell commands to the device(s). Be wary when sending shell " +
                        "commands, you can make instant changes or potentially harm the networking device. Care should be taken."
        }

        # stdout_queue is where the WorkerThread class will dump output to.
        self.stdout_queue = Queue.Queue()
        # thread will be the WorkerThread instantiation.
        self.thread = ""
        # boolean for tracking if the upper options of the GUI are shown.
        self.frames_shown = True

        # ## CREATE THE TOP MENUBAR OPTIONS
        self.menubar = tk.Menu(self)
        # tearoff=0 prohibits windows users from pulling out the menus.
        self.menu_file = tk.Menu(self.menubar, tearoff=0)
        self.menu_help = tk.Menu(self.menubar, tearoff=0)

        self.menubar.add_cascade(menu=self.menu_file, label="File")
        # Added space after Help to prevent OSX from putting spotlight in.
        self.menubar.add_cascade(menu=self.menu_help, label="Help ")

        # Create the File menu and appropriate keyboard shortcuts.
        self.menu_file.add_command(label="Save Template", accelerator='Ctrl-S',
                                   command=lambda: self.ask_template_save(None))
        self.bind_all("<Control-s>", self.ask_template_save)
        self.menu_file.add_command(label="Open Template", accelerator='Ctrl-O',
                                   command=lambda: self.ask_template_open(None))
        self.bind_all("<Control-o>", self.ask_template_open)
        self.menu_file.add_command(label="Set as Defaults",
                                   command=lambda: self.save_template(
                                   self.defaults_file, "defaults"))
        self.menu_file.add_separator()
        self.menu_file.add_command(label="Clear Fields", accelerator='Ctrl-F',
                                   command=lambda: self.clear_fields(None))
        self.bind_all("<Control-f>", self.clear_fields)
        self.menu_file.add_command(label="Clear Output", accelerator='Ctrl-W',
                                   command=lambda: self.clear_output(None))
        self.bind_all("<Control-w>", self.clear_output)
        self.menu_file.add_command(label="Run Script", accelerator='Ctrl-R',
                                   command=lambda: self.go(None))
        self.bind_all("<Control-r>", self.go)
        self.menu_file.add_separator()
        self.menu_file.add_command(label="Quit", accelerator='Ctrl-Q',
                                   command=lambda: self.quit(None))
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

        # ## FRAME INITIALIZATION
        # outer frame to hold the ip and creds frames
        self.ip_cred_frame = tk.Frame(self)

        self.ip_frame = tk.Frame(self.ip_cred_frame)
        self.creds_frame = tk.Frame(self.ip_cred_frame)
        # write to file frame
        self.wtf_frame = tk.Frame(self)
        self.options_frame = tk.Frame(self)
        # Set Commands frames for the additional commit options
        self.set_frame = tk.Frame(self.options_frame)
        self.set_frame_2 = tk.Frame(self.options_frame)
        self.help_frame = tk.Frame(self)
        self.buttons_frame = tk.Frame(self)
        self.output_frame = tk.Frame(self, bd=3, relief="groove")

        # #### Target device Section
        # string of actual IP or the file containing list of IPs
        self.ip_label = tk.Label(self.ip_frame, text="IP(s) / Host(s):")
        # Entry for IP or IP list
        self.ip_entry = JaideEntry(self.ip_frame)
        # Button to open file of list of IPs
        self.ip_button = tk.Button(self.ip_frame, text="Select File",
                                   command=lambda:
                                   self.open_file(self.ip_entry), takefocus=0)

        # ### TIMEOUTS AND PORT
        self.timeout_label = tk.Label(self.ip_frame, text="Session Timeout:")
        self.timeout_entry = JaideEntry(self.ip_frame, instance_type=int,
                                        contents=300)
        self.conn_timeout_label = tk.Label(self.ip_frame,
                                           text="Connection Timeout:")
        self.conn_timeout_entry = JaideEntry(self.ip_frame, instance_type=int,
                                             contents=5)

        # #### Authentication
        self.username_label = tk.Label(self.creds_frame, text="Username: ")
        self.username_entry = JaideEntry(self.creds_frame)
        self.password_label = tk.Label(self.creds_frame, text="Password: ")
        self.password_entry = JaideEntry(self.creds_frame, show="*")

        self.port_label = tk.Label(self.creds_frame, text="Port: ")
        self.port_entry = JaideEntry(self.creds_frame, instance_type=int,
                                     contents=22)

        # ## WRITE TO FILE
        self.wtf_entry = JaideEntry(self.wtf_frame)
        self.wtf_button = tk.Button(self.wtf_frame, text="Select File",
                                    command=self.open_wtf, takefocus=0)
        self.wtf_checkbox = JaideCheckbox(self.wtf_frame, text="Write to file",
                                          command=self.check_wtf, takefocus=0)
        self.wtf_radiobuttons = JaideRadiobutton(self.wtf_frame,
                                                 ["Single File",
                                                  "Multiple Files"],
                                                 ["s", "m"], takefocus=0)

        # ## OPTIONS
        # stores which option from options_list is selected
        self.option_value = tk.StringVar()
        # sets defaulted option to first one
        self.option_value.set(self.options_list[0])
        # Actual dropdown list widget. Uses PMW because tk base doesn't allow
        # an action to be bound to an option_menu.
        self.option_menu = Pmw.OptionMenu(self.options_frame,
                                          command=self.opt_select,
                                          menubutton_textvariable=self.option_value,
                                          items=self.options_list)
        # Prevents option_menu from taking focus while tabbing
        self.option_menu.component('menubutton').config(takefocus=0)
        self.option_entry = JaideEntry(self.options_frame)
        # format checkbox for operational commands
        self.format_box = JaideCheckbox(self.options_frame, text="Request XML Format", takefocus=0)

        # ## SCP OPTIONS
        self.scp_direction_value = tk.StringVar()
        self.scp_direction_value.set("Push")
        self.scp_direction_menu = tk.OptionMenu(self.options_frame,
                                                self.scp_direction_value,
                                                'Push', 'Pull')
        self.scp_source_button = tk.Button(self.options_frame,
                                           text="Local Source",
                                           command=lambda: self.open_file(self.option_entry),
                                           takefocus=0)
        self.scp_destination_button = tk.Button(self.options_frame,
                                                text="Local Destination",
                                                command=lambda: self.open_file(self.scp_destination_entry),
                                                takefocus=0)
        self.scp_destination_entry = JaideEntry(self.options_frame)

        # ## COMMIT OPTIONS
        self.set_list_button = tk.Button(self.options_frame,
                                         text="Select File",
                                         command=lambda: self.open_file(self.option_entry),
                                         takefocus=0)
        self.commit_check_button = JaideCheckbox(self.set_frame,
                                                 text="Check Only",
                                                 command=lambda: self.commit_option_update('check'),
                                                 takefocus=0)
        self.commit_blank = JaideCheckbox(self.set_frame_2, text="Blank",
                                          command=lambda: self.commit_option_update('blank'),
                                          takefocus=0)
        self.commit_confirmed_button = JaideCheckbox(self.set_frame,
                                                     text="Confirmed Minutes",
                                                     command=lambda: self.commit_option_update('confirmed'),
                                                     takefocus=0)
        self.commit_confirmed_min_entry = JaideEntry(self.set_frame,
                                                     contents="[1-60]")
        self.commit_synch = JaideCheckbox(self.set_frame_2, text="Synchronize",
                                          command=lambda: self.commit_option_update('synchronize'),
                                          takefocus=0)
        self.commit_comment = JaideCheckbox(self.set_frame_2, text="Comment",
                                            command=lambda: self.commit_option_update('comment'),
                                            takefocus=0)
        self.commit_comment_entry = JaideEntry(self.set_frame_2)
        self.commit_at = JaideCheckbox(self.set_frame, text="At Time",
                                       command=lambda: self.commit_option_update('at'),
                                       takefocus=0)
        self.commit_at_entry = JaideEntry(self.set_frame,
                                          contents="[yyyy-mm-dd ]hh:mm[:ss]")

        # ### Diff Config options
        self.diff_config_mode = tk.StringVar()
        self.diff_config_mode.set("Set")
        self.diff_config_menu = tk.OptionMenu(self.options_frame, self.diff_config_mode, "Set", "Stanza")

        # These are used to keep rows 1 and 2 of options_frame from being empty and thus hidden
        self.spacer_label = tk.Label(self.options_frame, takefocus=0)

        # Help label sits next in the target device section
        self.help_value = tk.StringVar("")
        self.help_label = tk.Label(self.help_frame, textvariable=self.help_value, justify="left", anchor="nw", wraplength=790)

        # ## Buttons
        self.go_button = tk.Button(self.buttons_frame, command=lambda:
                                   self.go(None), text="Run Script",
                                   takefocus=0)
        self.stop_button = tk.Button(self.buttons_frame, text="Stop Script",
                                     command=self.stop_script,
                                     state="disabled", takefocus=0)
        self.clear_button = tk.Button(self.buttons_frame, command=lambda:
                                      self.clear_output(None),
                                      text="Clear Output", state="disabled",
                                      takefocus=0)
        self.save_button = tk.Button(self.buttons_frame,
                                     command=self.save_output,
                                     text="Save Output", state="disabled",
                                     takefocus=0)
        self.toggle_frames_button = tk.Button(self.buttons_frame,
                                              command=self.toggle_frames,
                                              text="Toggle Options",
                                              takefocus=0)

        # ## SCRIPT OUTPUT AREA
        self.output_area = tk.Text(self.output_frame, wrap=tk.NONE)
        self.xscrollbar = AutoScrollbar(self.output_frame,
                                        command=self.output_area.xview,
                                        orient=tk.HORIZONTAL, takefocus=0)
        self.yscrollbar = AutoScrollbar(self.output_frame,
                                        command=self.output_area.yview,
                                        takefocus=0)
        self.output_area.config(yscrollcommand=self.yscrollbar.set,
                                xscrollcommand=self.xscrollbar.set,
                                takefocus=0)

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
        # ## INITIALIZE THE LAYOUT
        self.show_frames()
        self.rowconfigure(9, weight=1)
        self.columnconfigure(0, weight=1)
        self.output_frame.rowconfigure(0, weight=1)
        self.output_frame.columnconfigure(0, weight=1)

        # ## GRIDDING FOR ALL WIDGETS VISIBLE AT FIRST LOAD.
        # Section 0 - Target Device(s) - ip_frame
        self.ip_frame.grid(column=0, row=0, sticky="NW")
        self.ip_label.grid(column=0, row=0, sticky="NW")
        self.ip_entry.grid(column=1, row=0, sticky="NW")
        self.ip_button.grid(column=2, row=0, sticky="NW")
        self.timeout_label.grid(column=0, row=1, sticky="NW")
        self.timeout_entry.grid(column=1, row=1, sticky="NW")
        self.conn_timeout_label.grid(column=0, row=2, sticky="NW")
        self.conn_timeout_entry.grid(column=1, row=2, sticky="NW")
        self.sep1.grid(column=1, row=0, sticky="NS", padx=(18, 18))

        # Section 1 - Authentication - creds_frame
        self.creds_frame.grid(column=2, row=0, sticky="NW")
        self.username_label.grid(column=0, row=0, sticky="NW")
        self.username_entry.grid(column=1, row=0, sticky="NW")
        self.password_label.grid(column=0, row=1, sticky="NW")
        self.password_entry.grid(column=1, row=1, sticky="NW")
        self.port_label.grid(column=0, row=2, sticky="NW")
        self.port_entry.grid(column=1, row=2, sticky="NW")

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

        # Tie the commit options to the set_frame and set_frame_2
        self.commit_check_button.grid(column=0, row=0, sticky="NW")
        self.commit_confirmed_button.grid(column=3, row=0, sticky="NW")
        self.commit_blank.grid(column=3, row=0, sticky="NW")
        self.commit_synch.grid(column=0, row=0, sticky="NW")
        self.commit_comment.grid(column=1, row=0, sticky="NW")
        self.commit_comment_entry.grid(column=2, row=0, sticky="NW")
        self.commit_at.grid(column=1, row=0, sticky="NW")
        self.commit_at_entry.grid(column=2, row=0, sticky="NW")
        self.commit_confirmed_min_entry.grid(column=4, row=0, sticky="NW")
        # Set the window to a given size. This prevents autoscrollbar
        # 'fluttering' behaviour, and stabilizes the Toggle Output button.
        self.geometry('840x800')

        # Sets the tab order correctly
        self.ip_frame.lift()
        self.creds_frame.lift()
        self.wtf_frame.lift()
        self.options_frame.lift()

        # Run the opt_select method to ensure the proper fields are shown.
        self.opt_select(self.option_value.get())

        # Dictionary for reading and writing template files.
        self.template_opts = {
            "IP": self.ip_entry,
            "Timeout": self.timeout_entry,
            "Username": self.username_entry,
            "Password": self.password_entry,
            "WriteToFileBool": self.wtf_checkbox,
            "WriteToFileLoc": self.wtf_entry,
            "SingleOrMultipleFiles": self.wtf_radiobuttons,
            "Option": self.option_value,
            "FirstArgument": self.option_entry,
            "SCPDest": self.scp_destination_entry,
            "SCPDirection": self.scp_direction_value,
            "CommitCheck": self.commit_check_button,
            "CommitConfirmed": self.commit_confirmed_button,
            "CommitConfirmedMin": self.commit_confirmed_min_entry,
            "CommitBlank": self.commit_blank,
            "CommitAt": self.commit_at,
            "CommitAtTime": self.commit_at_entry,
            "CommitComment": self.commit_comment,
            "CommitCommentValue": self.commit_comment_entry,
            "CommitSynch": self.commit_synch,
            "Format": self.format_box,
            "DiffMode": self.diff_config_mode
        }

        # Load the defaults from file if defaults.ini exists
        if os.path.isfile(self.defaults_file):
            self.open_template(self.defaults_file, "defaults")

    def go(self, event):
        """ Purpose: This function is called when the user clicks on the 'Run Script' button. It inserts output
                   | letting the user know the script has started, spawns a subprocess running a WorkerThread instance.
                   | It also builds and presents the user with the jaide.py commmand,  and modifies the different buttons
                   | availability, now that the script has started.

            @param event: Any command that tkinter binds a keyboard shortcut to will receive the event
                        | parameter. It is a description of the keyboard shortcut that generated the event.
            @type event: Tkinter.event object
            @returns: None
        """
        # Ensure the input is valid.
        if self.input_validation():
            # puts cursor at end of text field
            self.output_area.mark_set(tk.INSERT, tk.END)
            self.write_to_output_area("****** Process Starting ******\n")

            # Gets username/ip from appropriate StringVars
            username = self.username_entry.get().strip()
            ip = self.ip_entry.get()
            timeout = self.timeout_entry.get()
            # if they are requesting xml.
            out_fmt = 'xml' if self.format_box.get() else 'text'
            # build the args translation array
            args_translation = {
                "Operational Command(s)": [self.option_entry.get().strip(),
                                           False, out_fmt],
                "Device Info": None,
                "Diff Config": [[self.option_entry.get(),
                                 self.diff_config_mode.get().lower()]],
                "Health Check": None,
                "Interface Errors": None,
                "Set Command(s)": [self.option_entry.get(),
                                   self.commit_check_button.get(),
                                   self.commit_confirmed_button.get(),
                                   self.commit_blank.get(),
                                   self.commit_comment_entry.get(),
                                   self.commit_at_entry.get(),
                                   self.commit_synch.get()],
                "SCP Files": [self.scp_direction_value.get(),
                              self.option_entry.get(),
                              self.scp_destination_entry.get(),
                              True, None],
                "Shell Command(s)": [self.option_entry.get().strip(),
                                     True, timeout]
            }
            # Looks up the selected option from dropdown against the conversion
            # dictionary to get the right Jaide function to call
            function = self.option_conversion[self.option_value.get()]

            # set the args to pass to the final function based on their choice.
            argsToPass = args_translation[self.option_value.get()]

            # # start building the jaide command to let the user know how they
            # # can use the CLI tool to do the same thing.
            # jaide_command = 'python jaide_cli.py -u ' + username + ' -i ' + ip
            # options = {
            #     "Diff Config": ' -d ',
            #     "Operational Command(s)": ' -c ',
            #     "Interface Errors": ' -e ',
            #     "Health Check": ' --health ',
            #     "Device Info": ' --info ',
            #     "Set Command(s)": ' -s ',
            #     "SCP Files": ' --scp ',
            #     "Shell Command(s)": ' --shell '
            # }
            # # add the argument flag for their choice in the optionMenu
            # jaide_command += options[self.option_value.get()]

            # # Logic to pass appropriate variables to WorkerThread for subsequent Jaide call
            # # SCP passes a dictionary which WorkerThread has logic to pull from. Done this way because the
            # # args in Jaide.copy_file are different than the ordering and needs of jaide.do_netconf() for other commands.
            # if self.option_value.get() == "SCP Files":
            #     argsToPass = {
            #         "scp_source": self.option_entry.get(),
            #         "scp_dest": self.scp_destination_entry.get(),
            #         "direction": self.scp_direction_value.get(),
            #         "write": True,
            #         "callback": None,
            #         "multi": True
            #     }
            #     jaide_command += self.scp_direction_value.get() + ' ' + self.option_entry.get() + ' ' + self.scp_destination_entry.get()
            # # List of args that can be easily unpacked by jaide.do_netconf
            # elif self.option_value.get() == 'Set Command(s)':
            #     jaide_command += '\"' + self.option_entry.get() + '\"'
            #     if self.commit_confirmed_button.get():  # Commit Confirmed
            #         jaide_command += ' --confirm ' + str(self.commit_confirmed_min_entry.get())
            #         argsToPass = [self.option_entry.get(), False, int(self.commit_confirmed_min_entry.get()), False]
            #     elif self.commit_check_button.get():  # Commit Check
            #         jaide_command += ' --check '
            #         argsToPass = [self.option_entry.get(), True, False, False]
            #     elif self.commit_blank.get():  # Commit Blank.
            #         jaide_command = jaide_command.split('-s')[0] + '--blank '
            #         argsToPass = [self.option_entry.get(), False, False, True]
            #     else:  # Neither confirm, check or blank, just regular commit.
            #         argsToPass = [self.option_entry.get(), False, False, False]
            #     # Attach the inclusive commit options (comment, at time, and synch) to the argsToPass for the jaide command.
            #     # append the commit comment or None if there is no comment.
            #     if self.commit_comment.get():
            #         argsToPass.append(self.commit_comment_entry.get())
            #         jaide_command += ' --comment \"' + self.commit_comment_entry.get() + '\" '
            #     else:
            #         argsToPass.append(None)
            #     # append the commit at time or None if it is not a time delayed commit.
            #     if self.commit_at.get():
            #         argsToPass.append(self.commit_at_entry.get())
            #         jaide_command += ' --at \"' + self.commit_at_entry.get() + '\" '
            #     else:
            #         argsToPass.append(None)
            #     # always append the commit_synch value, since the jaide.make_commit() function is expecting a bool.
            #     argsToPass.append(self.commit_synch.get())
            #     if self.commit_synch.get():
            #         jaide_command += ' --synchronize '

            # elif self.option_value.get() == 'Shell Command(s)':
            #     jaide_command += '\"' + self.option_entry.get() + '\"'
            #     argsToPass = [self.option_entry.get().strip(), True, timeout]

            # # The only other option left in yes_options is "Operational Command(s)".
            # elif self.option_value.get() in self.yes_options:
            #     jaide_command += '\"' + self.option_entry.get() + '\"'
            #     if self.format_box.get():  # If they are requesting XML format
            #         jaide_command += ' -f xml'
            #         out_fmt = 'xml'
            #     else:
            #         out_fmt = 'text'
            #     argsToPass = [self.option_entry.get().strip(), False, out_fmt, timeout]

            # # If the function does not need any additional arguments
            # elif self.option_value.get() in self.no_options:
            #     argsToPass = None

            # # If we could not figure out what we're doing, error out instead of making bogus calls to doJaide()
            # # This really should never be a possibility, as long as we've coded the other parts of this if statement to catch everything.
            # else:
            #     self.write_to_output_area("We've hit an error parsing the command you entered. Our code must be terrible.")
            #     return

            # print the CLI command to the user so they know how about jaide.py
            # self.write_to_output_area('The following command can be used to do this same thing on the command line:\n\t%s' % jaide_command)
            # if "|" in jaide_command:
            #     self.write_to_output_area('Your CLI command will have pipes, \'|\'. Be wary of your environment and necessary escaping.' +
            #                               '\nCheck the working-with-pipes.html file in the examples folder for more information.')
            # self.write_to_output_area('\n')  # add an extra line to separate the CLI suggestion from the rest of the output.

            # TODO: hard setting conn_timeout and port for now, need to allow user to specifiy
            # Create the WorkerThread class to run the Jaide functions.
            self.thread = WorkerThread(
                argsToPass=argsToPass,
                sess_timeout=timeout,
                conn_timeout=self.conn_timeout_entry.get(),
                port=self.port_entry.get(),
                command=function,
                stdout=self.stdout_queue,
                ip=ip,
                username=username,
                password=self.password_entry.get().strip(),
                write_to_file=self.wtf_entry.get(),
                wtf_style=self.wtf_radiobuttons.get(),
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
                   | dumps the output to the output_area using the function write_to_output_area. If the process
                   | is no longer alive, it changes the activation of buttons, and lets the user know that the script
                   | is done.

            @returns: None
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

            @returns: True if all checks pass, False if any single check fails.
            @rtype: bool
        """
        # Making sure the user typed something into the IP field.
        if self.ip_entry.get() == "":
            tkMessageBox.showinfo("IP Entry", "Please enter an IP address or IP address list file.")
        # Ensure there is a value typed into the username and password fields.
        elif self.username_entry.get() == "" or self.password_entry.get() == "":
            tkMessageBox.showinfo("Credentials", "Please enter both a username and password.")
        # If the write to file box is checked, they must have something typed in for an output file.
        elif self.wtf_entry.get() == "" and self.wtf_checkbox.get():
            tkMessageBox.showinfo("Write to File", "When writing to a file, a filename must be specified.")
        # Ensure that if an option is chosen that requires extra input that they have something in the entry widget.
        elif self.option_value.get() in self.yes_options and self.option_entry.get() == "" and self.commit_blank.get() == 0:
            tkMessageBox.showinfo("Option Input", "You chose an option that requires extra input, and didn't specify any additional information. " +
                "For example, when selecting \"Operational Command(s)\", a command string must be typed into the entry box.")
        elif (self.option_value.get() == 'Set Command(s)' and self.commit_at.get()) and (self.commit_at_entry.get() == "" or (re.match(r'([0-2]\d)(:[0-5]\d){1,2}', self.commit_at_entry.get()) is None and re.match(r'\d{4}-[01]\d-[0-3]\d [0-2]\d:[0-5]\d(:[0-5]\d)?', self.commit_at_entry.get()) is None)):
            tkMessageBox.showinfo("Commit At Time", "The time value you wrote for commit at was not valid. It must be one of two formats (seconds are optional):\n'hh:mm[:ss]'\n'yyyy-mm-dd hh:mm[:ss]'")
        elif (self.option_value.get() == 'Set Command(s)' and self.commit_comment.get()) and (self.commit_comment_entry.get() == "" or '"' in self.commit_comment_entry.get()):
            tkMessageBox.showinfo("Commit Comment", "If commenting on the commit, you must specify a string, and it cannot contain double-quotes (\").")
        else:
            try:
                if self.option_value.get() == 'Set Command(s)' and self.commit_confirmed_button.get():
                    int(self.commit_confirmed_min_entry.get())
            except ValueError:
                tkMessageBox.showinfo("Commit Confirmed", "A Commit Confirmed value must be an integer between 1 and 60 minutes.")
            else:
                # Make sure the timeout value is a number.
                try:
                    isinstance(self.timeout_entry.get(), int)
                except ValueError:
                    tkMessageBox.showinfo("Timeout", "A timeout value must be an integer, in seconds.")
                else:  # They've passed all checks.
                    return True
        return False

    def show_about(self):
        """ Purpose: This will show the about text for the application.

            @returns: None
        """
        aboutInfo = tk.Toplevel()
        aboutInfoLabel = tk.Label(aboutInfo, text="The Jaide GUI Application is a GUI wrapper for the jaide.py script.\n"
            "Version 1.1.0\n\rContributors:\n Geoff Rhodes (https://github.com/geoffrhodes) and Nathan Printz (https://github.com/nprintz)" +
            "\n\rMore information about Jaide and the Jaide GUI can be found at https://github.com/NetworkAutomation/jaide\n\rThe compiled " +
            "versions for Windows or Mac can be found at:\nhttps://github.com/NetworkAutomation/jaide/releases/latest", padx=50, pady=50)
        aboutInfoLabel.pack()

    def show_help(self):
        """ Purpose: This is called when the user selects the 'Help Text' menubar option. It opens the README.html file
                   | in their default browser. If the file doesn't exist it opens the github readme page instead.

            @returns:
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
                    webbrowser.open('https://github.com/NetworkAutomation/jaide')
                except webbrowser.Error:
                    pass
        elif os.name == 'nt':
            readme += "\\README.html"
            if os.path.isfile(readme):
                os.startfile(readme)  # this works on windows, not sure why pylint shows an error.
            else:
                try:
                    webbrowser.open('https://github.com/NetworkAutomation/jaide')
                except webbrowser.Error:
                    pass
        elif os.name == 'posix':
            readme += "/README.html"
            if os.path.isfile(readme):
                subprocess.call(('xdg-open', readme))
            else:
                try:
                    webbrowser.open('https://github.com/NetworkAutomation/jaide')
                except webbrowser.Error:
                    pass

    def show_examples(self):
        """ Open the example folder or github page. """
        # Grab the directory that the script is running from.
        examples = module_path()
        # Determine our OS, attach readme.html to the path, and open that file.
        if sys.platform.startswith('darwin'):
            examples += "/examples/"
            if os.path.isdir(examples):
                subprocess.call(('open', examples))
            else:
                try:
                    webbrowser.open('https://github.com/NetworkAutomation/'
                                    'jaide/tree/master/examples')
                except webbrowser.Error:
                    pass
        elif os.name == 'nt':
            examples += "\\examples\\"
            if os.path.isdir(examples):
                os.startfile(examples)
            else:
                try:
                    webbrowser.open('https://github.com/NetworkAutomation/'
                                    'jaide/tree/master/examples')
                except webbrowser.Error:
                    pass
        elif os.name == 'posix':
            examples += "/examples/"
            if os.path.isdir(examples):
                subprocess.call(('xdg-open', examples))
            else:
                try:
                    webbrowser.open('https://github.com/NetworkAutomation/'
                                    'jaide/tree/master/examples')
                except webbrowser.Error:
                    pass

    def write_to_output_area(self, output):
        """
        Insert string at the end of the output_area, and scroll to the bottom.

        @param output: String of the output to dump to the output_area
        @type output: str or unicode

        @returns: None
        """
        if isinstance(output, basestring):
            if output[-1:] is not "\n":
                output += "\n"
            # SCP was putting None to the output queue and this throws an error with insert
            self.output_area.insert(tk.END, output)
            self.output_area.see(tk.END)

    def ask_template_save(self, event):
        """ Purpose: Asks for the filepath of where to save the template file. If they give us one, we pass it to the
                   | save_template() function to actually be opened.

            @param event: Any command that tkinter binds a keyboard shortcut to will receive the event
                        | parameter. It is a description of the keyboard shortcut that generated the event.
            @type event: Tkinter.event object
            @returns: None
        """
        return_file = tkFileDialog.asksaveasfilename()
        if return_file:
            self.save_template(return_file, "template")

    def save_template(self, filepath, filetype):
        """ Purpose: asks for a file name and writes all variable information to it.
                   | Passwords are obfuscated with Base64 encoding, but this is
                   | by no means considered secure.

            @param filepath: The filepath of the template file that we are opening to save to
                           | with the information from the objects in the GUI.
            @type filepath: str or unicode
            @param filetype: This should be a string of either "defaults" or "template". This is used to
                           | notify the user what type of file failed to open for writing in case of a problem.
            @type filetype: str or unicode
            @returns: None
         """
        try:
            output_file = open(filepath, 'wb')
        except IOError as e:
            self.write_to_output_area("Couldn't open file to save the " + filetype + " file. Attempted location: " +
                                      output_file + "\nError: \n" + str(e))
        else:
            # Write each template option in the dictionary to the template.
            for key, value in self.template_opts.iteritems():
                if key == "Password":  # passwords need to be encoded.
                    output_file.write(key + ":~:" + base64.b64encode(value.get()) + "\n")
                else:
                    output_file.write(key + ":~:" + str(value.get()) + "\n")
            output_file.close()

    def ask_template_open(self, event):
        """ Purpose: Asks for the filepath of a template file. If they give us one, we pass it to the
                   | open_template() function to actually be opened.

            @param event: Any command that tkinter binds a keyboard shortcut to will receive the event
                        | parameter. It is a description of the keyboard shortcut that generated the event.
            @type event: Tkinter.event object
            @returns: None
        """
        return_file = tkFileDialog.askopenfilename()
        if return_file:
            self.open_template(return_file, "template")

    def open_template(self, filepath, filetype):
        """ Purpose: Loads information from a template file and replaces the options in the GUI with that
                   | of the template file.

            @param filepath: The filepath of the template file that we are opening to read in and replace
                           | the options with the information from the template.
            @type filepath: str or unicode
            @param filetype: This should be a string of either "defaults" or "template". This is used to
                           | notify the user what type of file failed to load in case of a problem.
            @type filetype: str or unicode
            @returns: None
        """
        try:
            input_file = open(filepath, "rb")
        except IOError as e:
            self.write_to_output_area("Couldn't open " + filetype + " file to import values. Attempted file: " +
                                      filepath + " Error: \n" + str(e))
        else:
            try:
                # Read the template file and set the fields accordingly.
                for line in input_file.readlines():
                    line = line.split(':~:')
                    if line[0] == "SingleOrMultipleFiles":
                        self.template_opts[line[0]].set("key", line[1].rstrip())
                    elif line[0] == "Password":
                        self.password_entry.set(base64.b64decode(line[1].rstrip()))
                    else:
                        self.template_opts[line[0]].set(line[1].rstrip())
                # check the option menu, wtf, commit check, and commit confirmed to update the visible options.
                self.opt_select(self.option_value.get())
                self.check_wtf()
            except Exception as e:
                self.write_to_output_area("Could not open template. Error:\n" + str(e))
            finally:
                input_file.close()

    def stop_script(self):
        """ Purpose: Called to kill the subprocess 'jaide' which is actually running the jaide.py script.
                   | This is called when the user clicks on the Stop Script button.

            @returns: None
        """
        self.thread.kill_proc()
        self.write_to_output_area("\n****** Attempting to stop process ******")

    def opt_select(self, opt):
        """ Purpose: This is used to show and hide options as different items are selected from the drop down accordingly.

            @param opt: The name of the option chosen by the user. The PMWmenu object passes this automatically when
                      | the opt_select function is called by the act of choosing an option within the menu.
            @type opt: str
            @returns: None
        """
        # First thing we do is forget all placement and deselect options, then we'll update according to what they chose afterwards.
        self.format_box.grid_forget()
        self.set_frame.grid_forget()
        self.set_frame_2.grid_forget()
        self.option_entry.grid_forget()
        self.set_list_button.grid_forget()
        self.scp_source_button.grid_forget()
        self.scp_destination_entry.grid_forget()
        self.scp_destination_button.grid_forget()
        self.scp_direction_menu.grid_forget()
        self.spacer_label.grid_forget()
        self.diff_config_menu.grid_forget()
        # We only want to deselect the commit options if we're changing to something other than 'Set Command(s)'
        # This prevents these commit options from being cleared on loading a template/defaults file.
        if opt != "Set Command(s)":
            self.commit_check_button.deselect()
            self.commit_confirmed_button.deselect()
            self.commit_blank.deselect()
            self.commit_synch.deselect()
            self.commit_at.deselect()
            self.commit_comment.deselect()

        if opt == "------":
            self.option_value.set("Device Info")

        # SCP
        if opt == "SCP Files":
            self.scp_direction_menu.grid(column=1, columnspan=2, row=0, sticky="NW")
            self.option_entry.grid(column=0, row=1, sticky="NW")
            self.scp_source_button.grid(column=1, row=1, sticky="NW", padx=2)
            self.scp_destination_entry.grid(column=2, row=1, sticky="NW")
            self.scp_destination_button.grid(column=3, row=1, sticky="NW", padx=2)

        # Any option that requires a single text arg
        elif opt in self.yes_options:
            self.option_entry.grid(column=1, columnspan=2, row=0, sticky="NEW")

            # If we are getting a list of set command, show file open button and commit check / confirmed boxes
            if opt == "Set Command(s)":
                self.set_list_button.grid(column=3, row=0, sticky="NW", padx=2)
                self.set_frame.grid(column=0, columnspan=4, row=1, sticky="NW", pady=(2, 2))
                self.set_frame_2.grid(column=0, columnspan=4, row=2, sticky="NW", pady=(2, 2))
            else:
                self.spacer_label.grid(column=1, columnspan=2, row=1, sticky="NW")

            if opt == "Operational Command(s)":
                self.set_list_button.grid(column=3, row=0, sticky="NW", padx=2)
                self.format_box.grid(column=0, row=1, sticky="NW")
            elif opt == "Diff Config":
                self.diff_config_menu.grid(column=3, row=0, sticky="NW", padx=2)
        else:
            # No option
            self.spacer_label.grid(column=1, columnspan=2, row=1, sticky="NW")

        # Update the help text for the new command
        self.help_value.set(self.help_conversion[opt])
        time.sleep(.05)  # sleep needed to avoid artifacts when updating frames
        # Update the UI after we've made our changes
        self.update()

    def open_file(self, entry_object):
        """ Purpose: This method is used to prompt the user to find a file on their local machine that already exists. Once
                   | they've selected a file, we will put the full filepath to that file in the text entry object that was
                   | passed to this method. If the user does not specify a file (ie. presses the 'cancel' button on the
                   | dialog box), then we will not update the entry field, we do nothing.

            @param entry_object: This is the actual displayed Tkinter Entry object where the filepath
                               | that the user specifies will be dumped to.
            @type entry_object: Tkinter.Entry object
            @returns: None
        """
        # ask the user for a local file, and if they give us one, replace the passed entry field.
        return_file = tkFileDialog.askopenfilename()
        if return_file:
            # Deletes whatever is in the field currently
            entry_object.delete(0, tk.END)
            # Puts the selected file (w/ full path) in to field
            entry_object.insert(0, return_file)

    def open_wtf(self):
        """ Purpose: This will delete whatever is in the wtf_entry field, and prompt the user with a find file dialog box.
                   | Once they've found the file, it will insert that filepath into wtf_entry. This function is only called
                   | when the 'Select File' button next to wtf_entry is clicked.

            @returns: None
        """
        # Retrieve a filename from the user
        return_file = tkFileDialog.asksaveasfilename()
        if return_file:
            # removes everything in wtf_entry
            self.wtf_entry.delete(0, tk.END)
            # puts full path of selected file to save as in wtf_entry
            self.wtf_entry.insert(0, return_file)

    def check_wtf(self):
        """ Purpose: This function is called whenever the user clicks on the checkbox for writing output to a file. It will take the
                   | appropriate action based on whether the box was checked previously or not. If it is now checked, it
                   | will add the wtf_entry and wtf_button options for specifying a file to write the output to. If it is
                   | now unchecked, it will remove these two objects.
            @returns: None
        """
        # if WTF checkbox is checked, enable the Entry and file load button
        if self.wtf_checkbox.get() == 1:
            self.wtf_entry.grid(column=1, row=0)
            self.wtf_button.grid(column=2, row=0, sticky="NW", padx=2)
            self.wtf_radiobuttons.grid("index", 0, column=4, row=0, sticky="NSW")
            self.wtf_radiobuttons.grid("index", 1, column=5, row=0, sticky="NSW")

        # if WTF checkbox is not checked, re-disable the entry options
        if self.wtf_checkbox.get() == 0:
            self.wtf_entry.grid_forget()
            self.wtf_button.grid_forget()
            self.wtf_radiobuttons.grid_forget("index", 0)
            self.wtf_radiobuttons.grid_forget("index", 1)

    def commit_option_update(self, check_type):
        """ Purpose: This function is called when any of the commit option check boxes are clicked. Depending on which one we click, we
                   | deselect the other two, and forget or create the grid for the commit confirmed minutes entry as necessary.

            @param check_type: A string identifier stating which commit option is being clicked. We are expecting one of three
                             | options: 'blank', 'check', or 'confirmed'.
            @type check_type: str
            @returns: None
        """
        if check_type == 'blank' and self.commit_blank.get():
            self.commit_confirmed_button.deselect()
            self.commit_check_button.deselect()
        elif check_type == 'check' and self.commit_check_button.get():
            self.commit_confirmed_button.deselect()
            self.commit_blank.deselect()
            self.commit_at.deselect()
            self.commit_synch.deselect()
            self.commit_comment.deselect()
        elif check_type == 'confirmed' and self.commit_confirmed_button.get():
            self.commit_check_button.deselect()
            self.commit_blank.deselect()
            self.commit_at.deselect()
        elif check_type == 'at' and self.commit_at.get():
            self.commit_confirmed_button.deselect()
            self.commit_blank.deselect()
            self.commit_check_button.deselect()
        elif check_type == 'comment' and self.commit_comment.get():
            self.commit_check_button.deselect()
        elif check_type == 'synchronize' and self.commit_synch.get():
            self.commit_check_button.deselect()

    def clear_output(self, event):
        """ Purpose: This function is called by the 'clear output' button and is used to remove all text from the output window.

            @param event: Any command that tkinter binds a keyboard shortcut to will receive the event
                        | parameter. It is a description of the keyboard shortcut that generated the event.
            @type event: Tkinter.event object
            @returns: None
        """
        self.output_area.delete(1.0, tk.END)

    def save_output(self):
        """ Purpose: This function is called by the 'save output' button and is used to open a save file dialog box, and write
                   | the text within the output_area window to that file.

            @returns: None
        """
        return_file = tkFileDialog.asksaveasfilename()
        # If no file is chosen, do not try to open it.
        if return_file:
            try:
                outFile = open(return_file, 'w+b')  # 'w' will open for overwriting, 'b' is for windows compatibility
            except IOError:
                tkMessageBox.showinfo("Couldn't open file.", "The file you specified could not be opened for writing.")
            else:
                outFile.write(self.output_area.get(1.0, tk.END))
                outFile.close()

    def quit(self, event):
        """ Purpose: Quit the application, called on selecting File > Quit, or by pressing Ctrl-Q.

            @param event: Any command that tkinter binds a keyboard shortcut to will receive the event
                        | parameter. It is a description of the keyboard shortcut that generated the event.
            @type event: Tkinter.event object
            @returns: None
        """
        sys.exit(0)

    def clear_fields(self, event):
        """ Purpose: Clear all input fields. Called by hitting Ctrl-C or clicking the appropriate menu option in the file menu.

            @param event: Any command that tkinter binds a keyboard shortcut to will receive the event
                        | parameter. It is a description of the keyboard shortcut that generated the event.
            @type event: Tkinter.event object
            @returns: None
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
        self.commit_comment_entry.delete(0, tk.END)
        self.commit_at_entry.delete(0, tk.END)
        self.commit_check_button.deselect()
        self.commit_confirmed_button.deselect()
        self.commit_blank.deselect()
        self.commit_synch.deselect()
        self.commit_at.deselect()
        self.commit_comment.deselect()

    def show_frames(self):
        """ Purpose: This function grids all frames and separators. It is called by the Toggle Options button, and used by
                   | __init__() to create the frames on starting the program.

            @returns: None
        """

        self.ip_cred_frame.grid(row=0, column=0, sticky="NEW", padx=(25, 25), pady=(25, 0))
        self.sep2.grid(row=1, column=0, sticky="WE", pady=12, padx=12)

        self.wtf_frame.grid(row=2, column=0, sticky="NW", padx=(25, 0))
        self.sep3.grid(row=3, column=0, sticky="WE", pady=12, padx=12)

        self.options_frame.grid(row=4, column=0, sticky="NEW", padx=(25, 0))
        self.sep4.grid(row=5, column=0, sticky="WE", pady=12, padx=12)

        self.help_frame.grid(row=6, column=0, sticky="NW", padx=(25, 0))
        self.sep5.grid(row=7, column=0, sticky="WE", pady=12, padx=12)

        self.buttons_frame.grid(row=8, column=0, sticky="NW", padx=(25, 25), pady=(0, 10))
        self.output_frame.grid(row=9, column=0, padx=(25, 25), sticky="SWNE", pady=(0, 25))

        self.update()

    def toggle_frames(self):
        """ This function is called by toggle_frames_button to toggle whether non-output frames are shown.

            @returns: None
        """
        if self.frames_shown:
            self.ip_cred_frame.grid_forget()
            self.wtf_frame.grid_forget()
            self.help_frame.grid_forget()

            self.sep2.grid_forget()
            self.sep3.grid_forget()
            self.sep4.grid_forget()

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
