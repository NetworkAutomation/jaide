""" jaide_cli utilities for manipulating output colors. """
from colorama import Fore, init, Style
import re


def color(out_string, color="success"):
    """ Highlight string for terminal color coding.

    @param out_string: the string to be colored
    @type out_string: str
    @param color: a string signifying which color to use.
    @type color: str

    @returns: the modified string, including the ANSI/win32 color codes.
    @rtype: str
    """
    # TODO: migrate to 3 letter color code index, 'grn', 'yel', etc
    init()
    if color == 'error':
        return (Fore.RED + Style.BRIGHT + out_string + Fore.RESET +
                Style.NORMAL)
    if color == 'info':
        return (Fore.YELLOW + Style.BRIGHT + out_string + Fore.RESET +
                Style.NORMAL)
    return (Fore.GREEN + Style.BRIGHT + out_string + Fore.RESET +
            Style.NORMAL)


def strip_color(search):
    """ Remove ANSI color codes from string.

    Purpose: Removes ANSI codes from a string. We use this to clean output
           | from a jaide command before writing it to a file.
    @param search: The string to search through to remove any ANSI codes.
    @type search: str

    @returns: The new string without any ANSI codes.
    @rtype: str
    """
    ansi_escape = re.compile(r'\x1b[^m]*m')
    return ansi_escape.sub('', search)


def color_diffs(string):
    """ Add color ANSI codes for diff lines.

    Purpose: Adds the ANSI/win32 color coding for terminal output to output
           | produced from difflib.

    @param string: The string to be replacing
    @type string: str

    @returns: The new string with ANSI codes injected.
    @rtype: str
    """
    string = string.replace('--- ', color('--- ', 'error'))
    string = string.replace('\n+++ ', color('\n+++ '))
    string = string.replace('\n-', color('\n-', 'error'))
    string = string.replace('\n+', color('\n+'))
    string = string.replace('\n@@ ', color('\n@@ ', 'info'))
    return string
