extern "C" int func_60194cbc(void *base, unsigned int bit) {
    return (((unsigned char *)base + (bit >> 3))[0x50] & (1 << (bit & 7))) != 0;
}