extern "C" int func_612c6c8c(void *self, int arg)
{
    unsigned char *p = (unsigned char *)self;
    int r0 = 0;
    if (*(unsigned char *)(p + 0xc) != 0)
        return r0;
    unsigned int *q = *(unsigned int **)(p + 0x8);
    if (q == 0)
        return r0;
    if (arg == 0)
        return r0;
    if (arg == 10)
        return *(int *)((char *)q + 0x5c);
    return *(int *)((char *)q + 0x60);
}