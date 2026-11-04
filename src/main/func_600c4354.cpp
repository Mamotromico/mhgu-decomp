extern "C" void func_600c4354(char *base, unsigned int flags) {
    if (flags & 1) {
        unsigned int *p = (unsigned int *)(base + 0x1408);
        unsigned int v = *p;
        v &= ~0x90u;
        *p = v;
        *(unsigned int *)(base + 0x1408 + 0xc) = 0;
    }
    if (flags & 2) {
        unsigned int *p = (unsigned int *)(base + 0x1408);
        unsigned int v = *p;
        v &= ~0xa0u;
        *p = v;
        *(unsigned int *)(base + 0x1408 + 0x10) = 0;
    }
}