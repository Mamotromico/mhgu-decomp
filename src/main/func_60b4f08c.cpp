extern "C" int func_60b4f08c(unsigned char *p) {
    unsigned *q = *(unsigned **)(p + 0x64);
    if (!q) {
        return 0;
    }
    unsigned v = *(unsigned *)((char *)q + 0x10);
    unsigned char *r = (unsigned char *)q + (v << 5);
    if (!v) {
        return (int)(unsigned)v;
    }
    return (int)(unsigned long)(r + 0x18);
}