"""The functions in this module allow compression and decompression using the
Brotli library.
"""
from ._brotli_cffi import ffi, lib


__version__ = ffi.string(lib.__version__)

MODE_GENERIC = lib.MODE_GENERIC
MODE_TEXT    = lib.MODE_TEXT
MODE_FONT    = lib.MODE_FONT

class error(Exception):
    pass

_valid_modes = set((MODE_GENERIC, MODE_TEXT, MODE_FONT))
_valid_quality = set(range(12))
_valid_lgwin = set(range(10, 25))
_valid_lgblock = set(range(16, 25)).union([0])


def compress(string, mode=MODE_GENERIC, quality=11, lgwin=22, lgblock=0):
    """Compress a byte string.

Signature:
  compress(string, mode=MODE_GENERIC, quality=11, lgwin=22, lgblock=0)

Args:
  string (bytes): The input data.
  mode (int, optional): The compression mode can be MODE_GENERIC (default),
    MODE_TEXT (for UTF-8 format text input) or MODE_FONT (for WOFF 2.0). 
  quality (int, optional): Controls the compression-speed vs compression-
    density tradeoff. The higher the quality, the slower the compression.
    Range is 0 to 11. Defaults to 11.
  lgwin (int, optional): Base 2 logarithm of the sliding window size. Range
    is 10 to 24. Defaults to 22.
  lgblock (int, optional): Base 2 logarithm of the maximum input block size.
    Range is 16 to 24. If set to 0, the value will be set based on the
    quality. Defaults to 0.

Returns:
  The compressed byte string.

Raises:
  brotli.error: If arguments are invalid, or compressor fails."""

    if mode not in _valid_modes:
        raise error("Invalid mode")
    if quality not in _valid_quality:
        raise error("Invalid quality. Range is 0 to 11.")
    if lgwin not in _valid_lgwin:
        raise error("Invalid lgwin. Range is 10 to 24.")
    if lgblock not in _valid_lgblock:
        raise error("Invalid lgblock. Can be 0 or in range 16 to 24.")

    length = len(string)
    output_length = int(1.2 * length + 10240);
    output = ffi.new("uint8_t[]", output_length)
    p_output_length = ffi.new("size_t[1]", [output_length])
    ok = lib.do_compress(mode, quality, lgwin, lgblock,
                         length, string,
                         p_output_length, output)
    if not ok:
        raise error("BrotliCompressBuffer failed")
    return ffi.buffer(output, p_output_length[0])[:]


@ffi.callback("int callback(void *, const uint8_t *, size_t)")
def _decompress_callback(data, output, output_size):
    buf = ffi.buffer(output, output_size)[:]
    ffi.from_handle(data).append(buf)
    return output_size


def decompress(string):
    """Decompress a compressed byte string.

Signature:
  decompress(string)

Args:
  string (bytes): The compressed input data.

Returns:
  The decompressed byte string.

Raises:
  brotli.error: If decompressor fails."""

    output_pieces = []
    ok = lib.do_decompress(string, len(string), _decompress_callback,
                           ffi.new_handle(output_pieces))
    if not ok:
        raise error("BrotliDecompress failed")
    return b''.join(output_pieces)
