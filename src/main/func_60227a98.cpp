extern "C" int func_60227a98(char *base)
{
    int result = 0;
    void *p = *(void **)(base + 0x208);
    if (p == 0)
        return result;

    unsigned int v = *(unsigned int *)((char *)p + 0xe8);
    unsigned int idx = v - 2;
    if (idx > 9)
        return result;

    unsigned int mask = 0x3e1u;
    idx &= 0x3ffu;
    if ((mask >> idx) & 1u)
        ;
    else
        return result;

    unsigned char b = *(unsigned char *)(base + 0x640);
    result = 0;
    if (b == 0)
        result = 1;

    return result;
}