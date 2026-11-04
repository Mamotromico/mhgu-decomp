extern "C" int func_605249f4(const char *base, unsigned int i, unsigned int bit) {
    if (i - 1 > 4)
        return 0;
    const unsigned int *p = (const unsigned int *)(base + (i - 1) * 0x360 + (bit >> 5) * 4 + 0x16c8);
    unsigned int v = *p;
    v &= 1u << (bit & 0x1f);
    return v != 0 ? 1 : 0;
}