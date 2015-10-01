import cffi

ffi = cffi.FFI()


ffi.cdef("""
static const int MODE_GENERIC, MODE_TEXT, MODE_FONT;
static int do_compress(int mode, int quality, int lgwin, int lgblock,
                       size_t length, uint8_t *input,
                       size_t *p_output_length, uint8_t *output);
static int do_decompress(uint8_t *input, size_t length,
                         int callback(void *, const uint8_t *, size_t),
                         void *callback_data);
""")


ffi.set_source("_brotli_cffi", """
#include <memory>
#include "../../enc/encode.h"
#include "../../dec/decode.h"

using namespace brotli;

static const int MODE_GENERIC = (int) BrotliParams::Mode::MODE_GENERIC;
static const int MODE_TEXT    = (int) BrotliParams::Mode::MODE_TEXT;
static const int MODE_FONT    = (int) BrotliParams::Mode::MODE_FONT;

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

""", source_extension='.cpp',
     sources=["../../enc/backward_references.cc",
              "../../enc/block_splitter.cc",
              "../../enc/brotli_bit_stream.cc",
              "../../enc/encode.cc",
              "../../enc/entropy_encode.cc",
              "../../enc/histogram.cc",
              "../../enc/literal_cost.cc",
              "../../enc/metablock.cc",
              "../../enc/static_dict.cc",
              "../../enc/streams.cc",
              "../../enc/utf8_util.cc",
              "../../dec/dictionary.c",
              "../../dec/bit_reader.c",
              "../../dec/decode.c",
              "../../dec/huffman.c",
              "../../dec/streams.c",
              "../../dec/state.c",
    ])


if __name__ == '__main__':
    ffi.compile()
