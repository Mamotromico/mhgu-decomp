extern "C" int func_60522d30(unsigned char *base, unsigned int bit) {
    if (bit == 0) return 0;
    unsigned int word = bit >> 5;
    unsigned int shift = bit & 0x1f;
    unsigned int val = *(unsigned int *)(base + 0x420 + word * 4);
    return (val & (1u << shift)) != 0;
}