extern "C" unsigned func_60283254(unsigned char *p, unsigned a, unsigned b, unsigned c) {
    unsigned x = *(unsigned *)(p + 0x251c) & c;
    unsigned y = *(unsigned *)(p + 0x2518) & b;
    unsigned r = y | x;
    if (r != 0) r = 1;
    return r;
}