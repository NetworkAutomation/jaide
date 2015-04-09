""" jaide_cli utilities for manipulating output colors. """
from colorama import Fore, init, Style
import re


def color(out_string, color='grn'):
    """ Highlight string for terminal color coding.

    @param out_string: the string to be colored
    @type out_string: str
    @param color: a string signifying which color to use.
    @type color: str

    @returns: the modified string, including the ANSI/win32 color codes.
    @rtype: str
    """
    c = {
        'blk': Fore.BLACK,
        'blu': Fore.BLUE,
        'cyn': Fore.CYAN,
        'grn': Fore.GREEN,
        'mag': Fore.MAGENTA,
        'red': Fore.RED,
        'wht': Fore.WHITE,
        'yel': Fore.YELLOW,
    }
    init()
    return (c[color] + Style.BRIGHT + out_string + Fore.RESET + Style.NORMAL)
    # if color == 'yel':
    #     return (c[] + Style.BRIGHT + out_string + Fore.RESET +
    #             Style.NORMAL)
    # return (Fore.GREEN + Style.BRIGHT + out_string + Fore.RESET +
    #         Style.NORMAL)


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
    string = string.replace('--- ', color('--- ', 'red'))
    string = string.replace('\n+++ ', color('\n+++ '))
    string = string.replace('\n-', color('\n-', 'red'))
    string = string.replace('\n+', color('\n+'))
    string = string.replace('\n@@ ', color('\n@@ ', 'yel'))
    return string
