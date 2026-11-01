extern "C" unsigned int func_601668f0(void *a, void *b, int shift)
{
    if (b == 0)
        return 0;
    unsigned char v = *(unsigned char *)((char *)b + 0x8b8);
    unsigned int r = (unsigned int)v >> 4;
    r &= 1u << shift;
    r &= 7u;
    if (r != 0)
        r = 1;
    return r;
}