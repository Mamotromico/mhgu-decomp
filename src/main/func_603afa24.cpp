extern "C" unsigned func_603afa24(unsigned *p, unsigned x) {
    unsigned *q = (unsigned *)((char *)p + ((x >> 5) & 7) * 4);
    unsigned v = *(unsigned *)((char *)q + 0xc0);
    return (v & (1u << (x & 0x1f))) != 0;
}