extern "C" int func_600e7a6c(const char *a, unsigned int b) {
    unsigned short v;
    if (b > 2)
        return 0;
    v = *(const unsigned short *)(a + 0x242);
    return (v & (1u << b)) ? 1 : 0;
}