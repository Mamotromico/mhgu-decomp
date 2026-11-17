extern "C" unsigned func_60838750(char *);

extern "C" unsigned func_60cd27a8(char *p) {
    unsigned r4 = *(unsigned *)(p + 0x24);
    unsigned r0 = func_60838750(p + 0x28);
    return r4 - r0;
}