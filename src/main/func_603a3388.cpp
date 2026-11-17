extern "C" unsigned func_603a3388(unsigned *p)
{
    unsigned *q = *(unsigned **)((char *)p + 0xac);
    if (q == 0)
        return 0;
    unsigned *r = *(unsigned **)((char *)q + 0x2c);
    if (r == 0)
        return 0;
    extern unsigned func_6039cadc(unsigned *, unsigned);
    return func_6039cadc(r, 0);
}