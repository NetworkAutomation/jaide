#!/usr/bin/python
""" Script to create API documentation from our jaide files. """
import re


def form_rep(line, pfx=''):
    """ Replace doc comment syntax with markdown syntax.

    @param line: the line to work with
    @type line: str
    @param pfx: a string prefix to prepend to class or function definitions.
    @type pfx: str

    @returns: The modified line
    @rtype: str
    """
    # escape underscores (fixes __init__)
    line = re.sub(r'__(\w+)__', r'\\_\\_\1\\_\\_', line)
    # set up function definitions
    line = re.sub(r'def ([\\\w]+)\((.*)\)', r'{}**\1**(*\2*)'.format(pfx), line)
    # set up class definitions
    line = re.sub(r'class (\w+)\((.*)\)', r'*class* {}**\1**(*\2*)'.format(pfx), line)
    # remove empty parameters from injecting 2 asterisks.
    line = re.sub(r'\(\*\*\)', r'()', line)
    # move Purpose down a line for separation
    line = re.sub(r'> Purpose:', r'\n> __Purpose:__', line)
    # bold/italicize parameters, types, and returns
    line = re.sub(r'\@param (\w+)\b', r'* __\1__', line)
    line = re.sub(r'\@type (\w+)\b', '  1. _Type_', line)
    line = re.sub(r'> \@returns', r'\n> __Returns__', line)
    line = re.sub(r'\@rtype', r'_Return Type_', line)
    # properties
    line = re.sub(r'\@(\w+)\.setter', r'__\1__', line)
    return line


def parse_py(out_file, lines, start_pos, pfx=''):
    """ Parse a python file and generate the markdown for the API Reference.

    @param out_file: the output file pointer.
    @type out_file: file pointer
    @param lines: the list of lines that we are reading from the original python file.
    @type lines: list
    @param start_pos: the starting line number. Used to skip the first Doc Comment in the file.
    @type start_pos: int
    @param pfx: A string prefix to prepend to class or function definitions.
    @type pfx: str

    @returns: None
    """
    i = start_pos
    while i < len(lines):
        if lines[i].strip().startswith('"""'):
            # header lines
            if lines[i-2].strip() != '' and not lines[i-2].strip().startswith('@'):
                out_file.write(form_rep(lines[i-2].strip() + ' ' + lines[i-1].lstrip(), pfx))
            if lines[i-1].strip().startswith('def') or lines[i-1].strip().startswith('class'):
                out_file.write(form_rep(lines[i-1].lstrip(), pfx))
            # handles one liners
            if lines[i].rstrip().endswith('"""'):
                out_file.write('> ' + lines[i].strip()[3:-3] + '\n\n')
            # loop through the rest of the doc string til we hit """ again.
            else:
                out_file.write('> ' + lines[i].lstrip()[3:])
                j = i + 1
                # loop for all lines until finding """
                while not lines[j].strip().endswith('"""'):
                    if lines[j].lstrip().startswith('|'):
                        # skip empty lines (some have '| ', so length < 3)
                        if len(lines[j].strip()) < 3:
                            pass
                        else:
                            # strip off the '| ' from continuation lines.
                            out_file.write('> ' + lines[j].strip()[2:] + '\n')
                    else:
                        out_file.write(form_rep('> ' + lines[j].strip() + '\n'))
                    j += 1
                out_file.write('\n')
                i = j
        if '.setter' in lines[i].strip():
            out_file.write(form_rep('\n*Property* ' + lines[i].strip() + '\n'))
        i += 1


if __name__ == '__main__':
    # open the output file and write the header.
    out_file = open('api.md', 'w')
    out_file.write('API Reference  \n============  \n')

    # open and write the Reference material for core.py, utils.py, and color_utils.py
    out_file.write('\n## Jaide Class  \n')
    parse_py(out_file, open('../jaide/core.py').readlines(), 12)

    out_file.write('\n## Utility Functions  \n')
    parse_py(out_file, open('../jaide/utils.py').readlines(), 5, 'jaide.utils.')

    out_file.write('\n## Color Utility Functions  \n')
    parse_py(out_file, open('../jaide/color_utils.py').readlines(), 5, 'jaide.color_utils.')

    out_file.close()
