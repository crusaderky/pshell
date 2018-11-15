"""Functions for manipulating files
"""
import logging
from .open import pshell_open


__all__ = ('concatenate', )


def concatenate(input_fnames, output_fname, mode='w', **kwargs):
    """Concatenate files. Python equivalent of
    :command:`cat input_fnames[0] input_fnames[1] ... > output_fname`.

    :param input_fnames:
        sequence of str. Paths to one or more input text files, to be appended
        one after the other to the output.
    :param str output_fname:
        Path to output text file, which may or may not already exist.
    :param str mode:
        Mode for opening the output file e.g. 'w' or 'ab'.
        Defaults to text mode unless 'b' is explicitly declared.
    :param kwargs:
        Passed verbatim to all the underlying :func:`pshell.open` calls.
        Among other things, this means that this function can transparently
        deal with compressed files by inspecting their extension; different
        files can use different compression algorithms as long as you use
        ``compression='auto'`` (the default).

    If the output is opened in text mode, the inputs will be too; if any file
    does not terminate with ``\\n``, it will be added. If the output is opened
    in binary mode, the inputs will too; no extra bytes will be added between
    files.
    """
    logging.info("Appending files: %s to: %s", input_fnames, output_fname)

    if 'b' in mode:
        _concatenate_binary(input_fnames, output_fname, mode, **kwargs)
    else:
        _concatenate_text(input_fnames, output_fname, mode, **kwargs)


def _concatenate_binary(input_fnames, output_fname, mode, **kwargs):
    """Implementation of concatenate for binary files
    """
    with pshell_open(output_fname, mode, **kwargs) as ofh:
        for fname in input_fnames:
            with pshell_open(fname, 'rb', **kwargs) as ifh:
                for chunk in iter(lambda: ifh.read(65536), b''):
                    ofh.write(chunk)


def _concatenate_text(input_fnames, output_fname, mode, **kwargs):
    """Implementation of concatenate for text files
    """
    prepend_newline = False
    if 'a' in mode:
        # Check if the last line of the first file ends with a \n
        try:
            # Discard from kwargs all parameters that are only applicable
            # to text mode
            kwargs_peek = kwargs.copy()
            kwargs_peek.pop('newline', None)
            kwargs_peek.pop('encoding', None)
            kwargs_peek.pop('errors', None)

            with pshell_open(output_fname, 'rb', **kwargs_peek) as fh:
                # Read last character
                fh.seek(-1, 2)
                # Won't work with \r terminator, which nobody cares about
                # anyway. We really only care about \n (Unix and MacOSX)
                # and \r\n (Windows).
                prepend_newline = fh.read() != b'\n'
        except FileNotFoundError as e:
            logging.info("%s", e)
        except OSError:
            # Empty file
            logging.info("Empty file: %s", output_fname)

    with pshell_open(output_fname, mode, **kwargs) as ofh:
        if prepend_newline:
            ofh.write('\n')
        for fname in input_fnames:
            with pshell_open(fname, 'r', **kwargs) as ifh:
                for line in ifh:
                    ofh.write(line.rstrip('\r\n'))
                    ofh.write('\n')
