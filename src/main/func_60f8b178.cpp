extern "C" void func_60f8b178(char *a0, unsigned a1) {
    unsigned char *p = *(unsigned char **)(a0 + 0x1428);
    unsigned char v = p[0x1bb];
    v &= ~(3u << (a1 << 1));
    p[0x1bb] = v;
}