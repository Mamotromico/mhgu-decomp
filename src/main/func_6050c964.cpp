extern "C" unsigned int func_6050c964(unsigned char *base, int n) {
    unsigned int r0 = *(unsigned int *)(base + 0x46c);
    unsigned int r3 = 1u;
    int r2 = n - 2;
    int r1 = n - 1;
    if ((unsigned int)r2 < 3u)
        r3 = r3 << r1;
    r0 &= r3;
    if (r0 != 0)
        r0 = 1;
    return r0;
}