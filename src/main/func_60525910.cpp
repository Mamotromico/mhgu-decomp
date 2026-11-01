extern "C" int func_60525910(unsigned char *base, unsigned int bit)
{
    unsigned int word = bit >> 5;
    unsigned int shift = bit & 0x1f;
    unsigned int *p = (unsigned int *)(base + word * 4);
    unsigned int value = *(unsigned int *)((char *)p + 0x3660);
    unsigned int mask = 1u << shift;
    return (value & mask) ? 1 : 0;
}