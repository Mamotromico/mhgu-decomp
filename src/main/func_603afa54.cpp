extern "C" int func_603afa54(unsigned char *base, unsigned int x) {
    unsigned int val = *(unsigned int *)(base + 0xb8 + ((x >> 5) & 7) * 4);
    if ((val & (1u << (x & 0x1f))) != 0)
        return 1;
    return 0;
}