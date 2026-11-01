extern "C" int func_60524e08(const unsigned char *base, unsigned int bit)
{
    unsigned int word = bit >> 5;
    unsigned int off = bit & 0x1f;
    const unsigned char *p = base + word * 4;
    unsigned int v = *(const unsigned int *)(p + 0x35f0);
    unsigned int mask = 1u << off;
    unsigned int r = v & mask;
    return r != 0 ? 1 : 0;
}