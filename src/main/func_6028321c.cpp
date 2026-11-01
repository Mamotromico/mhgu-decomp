extern "C" void func_6028321c(unsigned char *base, unsigned int, unsigned int mask0, unsigned int mask1) {
    unsigned int *p = (unsigned int *)(base + 0x2510);
    unsigned int v0 = p[0];
    unsigned int v1 = p[1];
    unsigned long long out = (unsigned long long)(v0 & ~mask0) |
                             ((unsigned long long)(v1 & ~mask1) << 32);
    *(unsigned long long *)p = out;
}