extern "C" unsigned func_60149a60(char *p)
{
    unsigned v = *(unsigned *)(p + 0x3fbf0);
    unsigned q = (unsigned)(((unsigned long long)v * 0x51eb851fULL) >> 37);
    unsigned r = v % 100u;
    return v + 100u - r;
}