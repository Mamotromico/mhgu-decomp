extern "C" int func_60d48470(char *p)
{
    unsigned char b;
    unsigned char c;

    void *q = *(void **)(p + 0x1428);
    b = *(unsigned char *)((char *)q + 0x1bb);
    if (b != 4)
        return 0;

    void *r = *(void **)(p + 0xcac0);
    c = *(unsigned char *)((char *)r + 0x70);
    if (c != 0)
        return 1;
    return 0;
}