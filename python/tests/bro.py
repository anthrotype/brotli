#! /usr/bin/env python
"""bro %s -- compression/decompression utility using the Brotli algorithm."""

from __future__ import print_function
import getopt
import sys
import os
import brotli


__usage__ = """\
Usage: bro [--force] [--decompress] [--input filename] [--output filename]
    [--mode 'text'|'font'] [--transform] [--length <int>] [--bufsize <int>]"""

__version__ = '0.1'


BROTLI_MODES = {
    'text': brotli.MODE_TEXT,
    'font': brotli.MODE_FONT
}

MAX_BUFFER_SIZE = 1000000000  # 1 GB


def get_binary_stdio(stream):
    """ Return the specified standard input, output or errors stream as a
    'raw' buffer object suitable for reading/writing binary data from/to it.
    """
    assert stream in ['stdin', 'stdout', 'stderr'], "invalid stream name"
    stdio = getattr(sys, stream)
    if sys.version_info[0] < 3:
        if sys.platform == 'win32':
            # set I/O stream binary flag on python2.x (Windows)
            import msvcrt
            msvcrt.setmode(stdio.fileno(), os.O_BINARY)
        return stdio
    else:
        # get 'buffer' attribute to read/write binary data on python3.x
        if hasattr(stdio, 'buffer'):
            return stdio.buffer
        else:
            orig_stdio = getattr(sys, "__%s__" % stream)
            return orig_stdio.buffer


def decompress(data, output_length=None, max_bufsize=MAX_BUFFER_SIZE):
    """ Decompress the data. Set decoded buffer size to output_length.
    If output_length is None, try to calculate it using get_decompressed_size
    method. If the latter fails, do the decompression in a loop, increasing
    the buffer size until it reaches the 'max_bufsize' limit.
    """
    if output_length:
        return brotli.decompress(data, output_length)
    else:
        try:
            output_length = brotli.get_decompressed_size(data)
        except brotli.error as e:
            bufsize = 5*len(data)
            while bufsize < max_bufsize:
                try:
                    return brotli.decompress(data, bufsize)
                except brotli.error:
                    bufsize = bufsize*10
            raise brotli.error("maximum buffer size reached")
        else:
            return brotli.decompress(data, output_length)


def main(args):

    options = parse_options(args)

    if options.infile:
        if not os.path.isfile(options.infile):
            print('file "%s" not found' % options.infile, file=sys.stderr)
            sys.exit(1)
        with open(options.infile, "rb") as infile:
            data = infile.read()
    else:
        if sys.stdin.isatty():
            # interactive console, just quit
            usage()
        infile = get_binary_stdio('stdin')
        data = infile.read()

    if options.outfile:
        if os.path.isfile(options.outfile) and not options.force:
            print('output file exists')
            sys.exit(1)
        outfile = open(options.outfile, "wb")
    else:
        outfile = get_binary_stdio('stdout')

    try:
        if options.decompress:
            data = decompress(data, options.length, options.bufsize)
        else:
            data = brotli.compress(data, options.mode, options.transform)
    except brotli.error as e:
        print('[ERROR] %s: %s' % (e, options.infile or 'sys.stdin'),
              file=sys.stderr)
        sys.exit(1)

    outfile.write(data)
    outfile.close()


def parse_options(args):
    try:
        raw_options, dummy = getopt.gnu_getopt(
            args, "?hdi:o:fm:tl:b:",
            ["help", "decompress", "input=", "output=", "force", "mode=",
             "transform", "length=", "bufsize="])
    except getopt.GetoptError as e:
        print(e, file=sys.stderr)
        usage()
    options = Options(raw_options)
    return options


def usage():
    print(__usage__, file=sys.stderr)
    sys.exit(1)


class Options(object):

    def __init__(self, raw_options):
        self.decompress = self.force = self.transform = False
        self.infile = self.outfile = None
        self.mode = BROTLI_MODES['text']
        # decompressed length (in bytes)
        self.length = None
        # max buffer size if decompressed length is unknown (default 1GB)
        self.bufsize = MAX_BUFFER_SIZE
        for option, value in raw_options:
            if option in ("-h", "--help"):
                print(__doc__ % (__version__))
                print("\n%s" % __usage__)
                sys.exit(0)
            elif option in ('-d', '--decompress'):
                self.decompress = True
            elif option in ('-i', '--input'):
                self.infile = value
            elif option in ('-o', '--output'):
                self.outfile = value
            elif option in ('-f', '--force'):
                self.force = True
            elif option in ('-m', '--mode'):
                value = value.lower()
                if value not in ('text', 'font'):
                    print('mode "%s" not recognized' % value, file=sys.stderr)
                    usage()
                self.mode = BROTLI_MODES[value]
            elif option in ('-t', '--transform'):
                self.transform = True
            elif option in ('-l', '--length'):
                self.length = int(value)
            elif option in ('-b', '--bufsize'):
                self.bufsize = int(value)


if __name__ == '__main__':
    main(sys.argv[1:])
