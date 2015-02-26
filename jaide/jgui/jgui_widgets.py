""" This Class is part of the jaide/jgui project.

It is free software for use in manipulating junos devices. More information
can be found at the github page found here:

    https://github.com/NetworkAutomation/jaide

The classes in this file are used to extend Tkinter's base functionality and
provide variables for tracking the value of widget within widget itself. The
JaideEntry class documented here below is an example of doing that by using
the self.contents variable to track the value of the text within the entry
widget. The JaideCheckbox class does this same with self.contents acting as
a Tkinter.IntVar to store the boolean integer of whether or not the
checkbox is checked.
"""
import Tkinter as tk


class JaideEntry(tk.Entry):

    """ Store value inside the entry object itself.

    The JaideEntry class inherits and extends the the Tkinter.Entry so we
    can define a common variable used for the value of the entry widget.
    The Tkinter.Entry class does not do this in and of itself, it only
    lets you specify another variable where you can store this information.
    """

    def __init__(self, parent, contents=None, instance_type=str, **kw):
        """ Initialize the tk.Entry field and set our custom value. """
        if instance_type is str:
            self.contents = tk.StringVar()
        elif instance_type is int:
            self.contents = tk.IntVar()
        else:
            self.contents = tk.StringVar()
        # now that the contents variable is set, initialize the object as a
        # Tkinter.Entry object.
        tk.Entry.__init__(self, parent, kw, textvariable=self.contents)
        if contents:  # Set the value of contents if they passed it.
            self.contents.set(contents)

    def get(self):
        """ Getter for the value of the Entry field. """
        return self.contents.get()

    def set(self, value):
        """ Setter for the value of the JaideEntry widget. """
        self.contents.set(value)


class JaideCheckbox(tk.Checkbutton):

    """ Adds integer variable to tk.Checkbutton.

    The JaideCheckbox class inherits and extends the Tkinter.Checkbutton
    class so we can automatically tie an integer variable to the
    checkbutton, reducing bloat within the JaideGUI class.
    """

    def __init__(self, parent, **kw):
        """ Initialize the checkbutton and set the integer variable. """
        self.contents = tk.IntVar()
        tk.Checkbutton.__init__(self, parent, kw, variable=self.contents)

    def get(self):
        """ Retrieve the integer value of the checkbox. """
        return self.contents.get()

    def set(self, value):
        """ Set the value of the checkbox. """
        self.contents.set(value)


class JaideRadiobutton():

    """ Extend Tkinter.Radiobutton to assign a variable for the value. """

    def __init__(self, parent, text, values, **kw):
        """ Handle a group of radio buttons with a single object.

        @param text: A list with each element being a string containing the
                   | display text for one of the radio buttons.
        @type value: list of strings
        @param values: A list of either strings or ints containing the return
                     | value for each radio button. Index must match text.
        @type values: list of integers or strings
        @param **kw: Allows for passing of other arguments to the constructor
                   | of the tk.Radiobuttons. Will be applied to all buttons.
        """
        self.Radiobuttons = []
        self.parent = parent
        self.text = text
        self.values = values
        if isinstance(text[0], basestring):
            self.contents = tk.StringVar()
        elif isinstance(text[0], int):
            self.contents = tk.IntVar()
        for x in range(len(text)):
            self.Radiobuttons.append(tk.Radiobutton(
                parent, text=text[x], value=values[x], variable=self.contents,
                **kw))
        self.Radiobuttons[0].select()

    def get(self):
        """ Return the value of the currently selected radio button. """
        return self.contents.get()

    def grid(self, indextype, index, **kw):
        """ Grid the selected tkinter radiobutton with the passed kwargs.

        @param indextype: string of either index or key
        @param index: either the number index in the list passed for
                    | text/value or the value itself referencing the
                    | radiobutton
        """
        if indextype == "index":
            self.Radiobuttons[index].grid(**kw)
        if indextype == "key":
            self.Radiobuttons[self.values.index(index)].grid(**kw)

    def grid_forget(self, indextype, index):
        """ Forget gridding on the selected radiobutton.

        @param indextype: string of either index or key
        @param index: either the number index in the list passed for
                    | text/value or the value itself
                    | referencing the radiobutton
        """
        if indextype == "index":
            self.Radiobuttons[index].grid_forget()
        if indextype == "key":
            self.Radiobuttons[self.values.index(index)].grid_forget()

    def set(self, indextype, index):
        """ Setter for the selected radiobutton.

        @param indextype: string of either index or key
        @param index: either the number index in the list passed for
                    | text/value or the value itself
                    | referencing the radiobutton
        """
        if indextype == "index":
            self.Radiobuttons[index].select()
        if indextype == "key":
            self.Radiobuttons[self.values.index(index)].select()


class AutoScrollbar(tk.Scrollbar):

    """ A scrollbar that hides itself if it's not needed.

    Only works if you use the grid geometry manager.

    Utilized from http://effbot.org/zone/tk-autoscrollbar.htm
    """

    def set(self, lo, hi):
        """ Remove the grid of itself if necessary. """
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from tk!
            self.grid_remove()
        else:
            self.grid()
        tk.Scrollbar.set(self, lo, hi)
