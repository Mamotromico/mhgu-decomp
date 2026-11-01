extern "C" int func_60524c50(char *base, unsigned int bit) {
    unsigned int word = bit >> 5;
    unsigned int shift = bit & 0x1f;
    unsigned int *p = (unsigned int *)(base + word * 4);
    unsigned int val = *(unsigned int *)((char *)p + 0x349c);
    return (val & (1u << shift)) != 0;
}