import cffi
import os


CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

MODULE_NAME = "_brotli_cffi"
PACKAGE_DIR = "python/lib"


ffi = cffi.FFI()


ffi.cdef("""
static const char* __version__;
static const int MODE_GENERIC, MODE_TEXT, MODE_FONT;
static int do_compress(int mode, int quality, int lgwin, int lgblock,
                       size_t length, uint8_t *input,
                       size_t *p_output_length, uint8_t *output);
static int do_decompress(uint8_t *input, size_t length,
                         int callback(void *, const uint8_t *, size_t),
                         void *callback_data);
""")


ffi.set_source('brotli.'+MODULE_NAME, """
#include <memory>
#include <enc/encode.h>
#include <dec/decode.h>
#include <tools/version.h>

using namespace brotli;

static const char* __version__ = BROTLI_VERSION;

static const int MODE_GENERIC = (int) BrotliParams::MODE_GENERIC;
static const int MODE_TEXT    = (int) BrotliParams::MODE_TEXT;
static const int MODE_FONT    = (int) BrotliParams::MODE_FONT;

static int do_compress(int mode, int quality, int lgwin, int lgblock,
                       size_t length, uint8_t *input,
                       size_t *p_output_length, uint8_t *output)
{
    BrotliParams params;
    params.mode = (BrotliParams::Mode)mode;
    params.quality = quality;
    params.lgwin = lgwin;
    params.lgblock = lgblock;
    return BrotliCompressBuffer(params, length, input,
                                p_output_length, output);
}

static int do_decompress(uint8_t *input, size_t length,
                         int callback(void *, const uint8_t *, size_t),
                         void *callback_data)
{
    BrotliMemInput memin;
    BrotliInput in = BrotliInitMemInput(input, length, &memin);

    BrotliOutput out;
    out.cb_ = callback;
    out.data_ = callback_data;

    return BrotliDecompress(in, out);
}

""",
    source_extension='.cpp',
    sources=[
        "enc/backward_references.cc",
        "enc/block_splitter.cc",
        "enc/brotli_bit_stream.cc",
        "enc/encode.cc",
        "enc/entropy_encode.cc",
        "enc/histogram.cc",
        "enc/literal_cost.cc",
        "enc/metablock.cc",
        "enc/static_dict.cc",
        "enc/streams.cc",
        "enc/utf8_util.cc",
        "dec/bit_reader.c",
        "dec/decode.c",
        "dec/dictionary.c",
        "dec/huffman.c",
        "dec/streams.c",
        "dec/state.c",
    ],
    depends=[
        "enc/backward_references.h",
        "enc/bit_cost.h",
        "enc/block_splitter.h",
        "enc/brotli_bit_stream.h",
        "enc/cluster.h",
        "enc/command.h",
        "enc/context.h",
        "enc/dictionary.h",
        "enc/dictionary_hash.h",
        "enc/encode.h",
        "enc/entropy_encode.h",
        "enc/fast_log.h",
        "enc/find_match_length.h",
        "enc/hash.h",
        "enc/histogram.h",
        "enc/literal_cost.h",
        "enc/metablock.h",
        "enc/port.h",
        "enc/prefix.h",
        "enc/ringbuffer.h",
        "enc/static_dict.h",
        "enc/static_dict_lut.h",
        "enc/streams.h",
        "enc/transform.h",
        "enc/types.h",
        "enc/utf8_util.h",
        "enc/write_bits.h",
        "dec/bit_reader.h",
        "dec/context.h",
        "dec/decode.h",
        "dec/dictionary.h",
        "dec/huffman.h",
        "dec/prefix.h",
        "dec/port.h",
        "dec/streams.h",
        "dec/transform.h",
        "dec/types.h",
        "dec/state.h",
        "tools/version.h",
    ],
    include_dirs=["."]
  )


if __name__ == '__main__':
    import sysconfig
    import shutil

    # cd .. to where setup.py is located
    build_dir = os.path.dirname(CURR_DIR)
    os.chdir(build_dir)

    # compile extension module here
    ffi.compile('.')

    # move compiled module inside package dir
    ext_file = MODULE_NAME + sysconfig.get_config_var('SO')
    dest = os.path.join(PACKAGE_DIR, 'brotli', ext_file)
    if os.path.exists(ext_file):
        if os.path.exists(dest):
            os.remove(dest)
        shutil.move(ext_file, dest)
