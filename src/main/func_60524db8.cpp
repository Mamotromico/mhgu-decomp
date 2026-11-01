extern "C" int func_60524db8(unsigned char *base, unsigned int bit) {
    unsigned int word = bit >> 5;
    unsigned int b = bit & 0x1f;
    unsigned int val = *(unsigned int *)(base + word * 4 + 0x35a8);
    val &= 1u << b;
    return val != 0 ? 1 : 0;
}