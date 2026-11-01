extern "C" int func_60524c78(unsigned char *p, unsigned int bit) {
    unsigned int word_index = bit >> 5;
    unsigned int bit_index = bit & 0x1f;
    const unsigned int *base = (const unsigned int *)(p + word_index * 4);
    unsigned int value = base[0x34a0 / 4];
    unsigned int masked = value & (1u << bit_index);
    return masked != 0;
}