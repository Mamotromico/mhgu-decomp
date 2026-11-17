extern "C" unsigned func_60277848(unsigned a, unsigned b, unsigned c) {
    unsigned r0 = 0xff;
    if (c >= 0xb) {
        unsigned x = c - 0xb;
        r0 = (unsigned)(((unsigned long long)x * 0xaaaaaaabULL) >> 35);
    }
    unsigned r1 = (r0 == b) ? 1 : 0;
    unsigned r2 = (r0 == 0xff) ? 1 : 0;
    return r2 | r1;
}