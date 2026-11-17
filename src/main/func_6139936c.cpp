extern "C" int func_6139936c(unsigned char *p) {
    if (*(p + 0x14) == 0)
        return 0;
    unsigned v = *(unsigned *)(p + 0x34);
    v &= ~1u;
    return v == 4 ? 1 : 0;
}