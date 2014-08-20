Working with Jaide GUI
=================
There are two ways to use the Jaide GUI. The easiest is through the compiled applications for [Windows](https://github.com/geoffrhodes/jaide-windows-compile) and [Mac](https://github.com/geoffrhodes/jaide-osx-compile). By using the compiled application, you don't need to worry about any python requirements or ever touch the command line. Simply load the application and you're ready to start.  

The other manner is by using the command line to execute `python jgui.py` from the folder where `jgui.py`, `worker_thread.py`, and `jaide.py` exist. Since this uses your native python environment, you must initially obtain all pre-requisite modules for proper execution, just as if you were running jaide.py from the command line. All information about the prerequisite modules can be found in the README file. 

### Jaide GUI Unique functions  

#### Templates  

Templates are a very useful feature for saving a common scenario for repeated use. Simply set up all the options for an execution of the script, and then choose `File > Save Template` [Ctrl+S] from the menu to save those options to a file. They can then be loaded at a later time using `File > Open Template` [Ctrl+O]. 

**Note -** Passwords are stored in the template in a base64 encoded format. While this is not human readable, it should not be considered fully encrypted nor secure. If you do not want the password stored in this manner simply leave the password field blank when you save the template. 

#### Keyboard Shortcuts  

Any of the following keyboard shortcuts can be used to manipulate the GUI:  

| Shortcut | Function | Description |  
| -------- | -------- | ----------- |  
| Ctrl+S | Save Template | Used to save the current status of every option to a template file so it can be loaded later |  
| Ctrl+O | Open Template | Used to open a template file to retrieve the state of each option |  
| Ctrl+F | Clear Fields | Clears all option fields to give yourself a blank slate |  
| Ctrl+W | Clear Output | Clears the output area of all text |  
| Ctrl+R | Run Script | Executes the specified options and runs the script |  
| Ctrl+Q | Quit Jaide GUI | Exits the program |  
