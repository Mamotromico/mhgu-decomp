extern "C" unsigned func_60277888(unsigned unused, unsigned x)
{
    if (x < 0xb)
        return 0xff;
    unsigned n = x - 0xb;
    unsigned long long p = (unsigned long long)n * 0xaaaaaaabULL;
    return (unsigned)(p >> 32) >> 3;
}