extern "C" int func_60c6f01c(unsigned char *p)
{
    unsigned int *q;
    unsigned int v;

    q = *(unsigned int **)(p + 0x30);
    if (q == 0)
        return 0;
    q = *(unsigned int **)((unsigned char *)q + 0xf0);
    if (q == 0)
        return 0;
    if (*(unsigned char *)(p + 0x198) == 0)
        return 0;
    v = *(unsigned int *)(p + 0xc);
    return (v & 0x407) == 0x402;
}