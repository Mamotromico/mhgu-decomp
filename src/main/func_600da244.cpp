extern "C" int func_600da244(unsigned char *p, unsigned x) {
    unsigned v = *(unsigned *)(p + 0x0);
    int (*fn)(unsigned char *) = *(int (**)(unsigned char *))(v + 0x88);
    unsigned r = (unsigned)fn(p);
    unsigned one = (r <= x) ? 1u : 0u;
    return (int)one;
}