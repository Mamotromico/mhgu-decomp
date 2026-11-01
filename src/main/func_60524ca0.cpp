extern "C" int func_60524ca0(const char *base, unsigned int bit) {
    unsigned int word = *(const unsigned int *)(base + 0x3510 + ((bit >> 5) << 2));
    unsigned int mask = 1u << (bit & 0x1f);
    return (word & mask) != 0;
}