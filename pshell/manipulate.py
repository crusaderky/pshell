"""Functions for manipulating files
"""
import logging
from .open import open as pshell_open


def concatenate(output_fname, *input_fnames):
    """Concatenate files, Python equivalent of
    :command:`cat input_fnames[0] input_fnames[1] ... >> output_fname`.

    :param str output_fname:
        Path to output text file, which may or may not already exist.
        If it already exists, the new contents will be appended to it.
    :param str input_fnames:
        Path to one or more input text files, to be appended one after the
        other to the output
    """
    logging.info("Appending files: %s to: %s", input_fnames, output_fname)

    # Check if the last line of the first file ends with a \n
    try:
        with pshell_open(output_fname, 'rb') as fh:
            # Read last character
            fh.seek(-1, 2)
            prepend_newline = fh.read() != b'\n'
    except FileNotFoundError as e:
        logging.info("%s", e)
        prepend_newline = False
    except OSError:
        # Empty file
        logging.info("Empty file")
        prepend_newline = False

    with pshell_open(output_fname, 'a') as result:
        if prepend_newline:
            result.write('\n')
        for fname in input_fnames:
            with open(fname) as ifile:
                for line in ifile:
                    if not line.endswith('\n'):
                        line = line + '\n'
                    result.write(line)
