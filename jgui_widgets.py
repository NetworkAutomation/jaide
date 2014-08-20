""" These classes are used to extend Tkinter's base functionality and provide variables for tracking the value of widget within 
	widget itself. The JaideEntry class documented here below is an example of doing that by using the self.contents variable to
	track the value of the text within the entry widget. The JaideCheckbox class does this same with self.contents acting as a 
	Tkinter.IntVar to store the boolean integer of whether or not the checkbox is checked. 
"""
import Tkinter as tk


class JaideEntry(tk.Entry):
    """ The JaideEntry class inherits and extends the the Tkinter.Entry so we can define a common variable used for the value
        of the entry widget. The Tkinter.Entry class does not do this in and of itself, it only lets you specify another 
        variable where you can store this information. 
    """
    def __init__(self, parent, contents=None, instance_type=str, **kw):
        """ Init function for the class JaideEntry, which initializes a contents self variable for the purpose of storing and 
            retrieving the value within the entry widget. Without creating this, we'd have to use two variables for each 
            entry widget within the JaideGUI class. The contents parameter is used to set a value for the entry widget at the
            time of initialization. 
        """
        if instance_type is str:
            self.contents = tk.StringVar()
        elif instance_type is int:
            self.contents = tk.IntVar()
        else:
            self.contents = tk.StringVar()
        # now that the contents variable is set, initialize the object as a Tkinter.Entry object.
        tk.Entry.__init__(self, parent, kw, textvariable=self.contents)
        if contents:  # Set the value of contents if they passed it. 
            self.contents.set(contents)
            

    def get(self):
        """ This function is used to return the value of the entry object. """
        return self.contents.get()


    def set(self, value):
        """ Sets the value of the JaideEntry widget. """
        self.contents.set(value)


class JaideCheckbox(tk.Checkbutton):
    """ The JaideCheckbox class inherits and extends the Tkinter.Checkbutton class so we can automatically tie an integer variable
        to the checkbutton, reducing bloat within the JaideGUI class.
    """
    def __init__(self, parent, **kw):
        """ This initializes the checkbutton, creating the integer variable storing the value of whether or not the checkbox is checked.
        """
        self.contents = tk.IntVar()
        tk.Checkbutton.__init__(self, parent, kw, variable=self.contents)


    def get(self):
        """ Retrieve the integer value of the checkbox,  0 = unchecked, 1 = checked. """
        return self.contents.get()


    def set(self, value):
        """ Set the value of the checkbox to 0 or 1, thereby checking or unchecking it. """
        self.contents.set(value)


class AutoScrollbar(tk.Scrollbar):
    """ A scrollbar that hides itself if it's not needed. Only works if you use the grid geometry manager.
        Utilized from http://effbot.org/zone/tk-autoscrollbar.htm
    """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from tk!
            self.grid_remove()
        else:
            self.grid()
        tk.Scrollbar.set(self, lo, hi)
