extern "C" int func_60081744(unsigned char *p)
{
    unsigned char *base = p;
    if (*(unsigned char *)(base + 0x1409) & 0x40)
        return 0;
    unsigned int *q = *(unsigned int **)(base + 0x1428);
    unsigned char v = *(unsigned char *)((unsigned char *)q + 0x518);
    if (v == 1)
        return 1;
    return 0;
}