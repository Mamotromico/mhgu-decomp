extern "C" unsigned func_60524b34(unsigned char *base, unsigned index, unsigned bit) {
    unsigned char *p = base + index * 0xcc;
    unsigned *q = (unsigned *)(p + 0x2830 + (bit >> 5) * 4);
    return (*q >> (bit & 0x1f)) & 1 ? 1 : 0;
}