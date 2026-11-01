extern "C" int func_60524d90(const unsigned char *base, unsigned int bit) {
    unsigned int word = *(const unsigned int *)(base + ((bit >> 5) << 2) + 0x359c);
    return (word & (1u << (bit & 0x1f))) != 0;
}