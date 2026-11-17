extern "C" unsigned func_60b6a520(char *p, unsigned i)
{
    unsigned n = *(unsigned short *)(p + 0x104);
    if (n <= i)
        return 0xffff;
    unsigned short *q = *(unsigned short **)(p + 0x100);
    if (q == 0)
        return 0xffff;
    return q[i];
}