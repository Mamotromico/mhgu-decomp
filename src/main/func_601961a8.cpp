extern "C" unsigned func_604c90a4(unsigned);

extern "C" unsigned func_601961a8(unsigned *p)
{
    unsigned r = p[0x30 / 4];
    if (r == 0)
        return 0;
    return func_604c90a4(r);
}