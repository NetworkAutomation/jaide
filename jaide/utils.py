""" Jaide standalone utility functions. """

from os import path
from lxml import etree, objectify
import xml.etree.ElementTree as ET


def clean_lines(commands):
    """ Generate strings that are not comments or lines with only whitespace.

    Purpose: This function is a generator that will read in either a
           | plain text file of strings(IP list, command list, etc), a
           | comma separated string of strings, or a list of strings. It
           | will crop out any comments or blank lines, and yield
           | individual strings.
           |
           | Only strings that do not start with a comment '#', or are not
           | entirely whitespace will be yielded. This allows a file with
           | comments and blank lines for formatting neatness to be used
           | without a problem.

    @param commands: This can be either a string that is a file
                   | location, a comma separated string of strings
                   | ('x,y,z,1,2,3'), or a python list of strings.
    @type commands: str or list

    @returns: Yields each command in order
    @rtype: iterable of str
    """
    if isinstance(commands, basestring):
        # if the command argument is a filename, we need to open it.
        if path.isfile(commands):
            commands = open(commands, 'rb')
        # if the command string is a comma separated list, break it up.
        elif len(commands.split(',')) > 1:
            commands = commands.split(',')
        else:  # if a single command, need to just be returned.
            try:
                if commands.strip()[0] != "#":
                    yield commands.strip() + '\n'
                    return
            except IndexError:
                pass
    elif isinstance(commands, list):
        pass
    else:
        raise TypeError('clean_lines() accepts a \'str\' or \'list\'')
    for cmd in commands:
        # exclude commented lines, and skip blank lines (index error)
        try:
            if cmd.strip()[0] != "#":
                yield cmd.strip() + '\n'
        except IndexError:
            pass


def xpath(source_xml, xpath_expr, req_format='string'):
    """ Filter xml based on an xpath expression.

    Purpose: This function applies an Xpath expression to the XML
           | supplied by source_xml. Returns a string subtree or
           | subtrees that match the Xpath expression. It can also return
           | an xml object if desired.

    @param source_xml: Plain text XML that will be filtered
    @type source_xml: str or lxml.etree.ElementTree.Element object
    @param xpath_expr: Xpath expression that we will filter the XML by.
    @type xpath_expr: str
    @param req_format: the desired format of the response, accepts string or
                     | xml.
    @type req_format: str

    @returns: The filtered XML if filtering was successful. Otherwise,
            | an empty string.
    @rtype: str or ElementTree
    """
    tree = source_xml
    if not isinstance(source_xml, ET.Element):
        tree = objectify.fromstring(source_xml)
    # clean up the namespace in the tags, as namespaces appear to confuse
    # xpath method
    for elem in tree.getiterator():
        # beware of factory functions such as Comment
        if isinstance(elem.tag, basestring):
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i+1:]

    # remove unused namespaces
    objectify.deannotate(tree, cleanup_namespaces=True)
    filtered_list = tree.xpath(xpath_expr)
    # Return string from the list of Elements or pure xml
    if req_format == 'xml':
        return filtered_list
    matches = ''.join(etree.tostring(
        element, pretty_print=True) for element in filtered_list)
    return matches if matches else ""
