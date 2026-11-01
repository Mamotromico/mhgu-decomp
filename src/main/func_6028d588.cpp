extern "C" int func_6028d588(const char *base) {
    const unsigned short *p = (const unsigned short *)(base + 0x2506);
    unsigned short v = *p;
    if (v != 0x1000)
        return 0;
    unsigned int x = *(const unsigned int *)(base + 0x26e4);
    if (x != 1)
        return 0;
    return 1;
}