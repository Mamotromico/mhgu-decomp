struct Dest {
    unsigned char pad0[2];
    unsigned short half;
    unsigned int word;
};

struct Source {
    unsigned int word;
    unsigned short half;
};

extern "C" void func_613ef4a0(struct Dest **out, const struct Source *src)
{
    (*out)->word = __builtin_bswap32(src->word);
    (*out)->half = __builtin_bswap16(src->half);
}