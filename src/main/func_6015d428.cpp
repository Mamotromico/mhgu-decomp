extern "C" unsigned func_6015b1a4(unsigned, unsigned);

extern "C" unsigned func_6015d428(unsigned *p, unsigned v)
{
    unsigned *q = *(unsigned **)((char *)p + 0x1c);
    if (q && *(unsigned *)((char *)q + 0x64) > v)
        return func_6015b1a4((unsigned)q, v);
    return 0;
}