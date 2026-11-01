extern "C" unsigned int func_61398da4(unsigned char *p, int bit)
{
    unsigned int v;
    if (bit > 0x1f)
        return 0;
    v = *(unsigned int *)(p + 8);
    v &= 1u << bit;
    return v != 0 ? 1u : 0u;
}