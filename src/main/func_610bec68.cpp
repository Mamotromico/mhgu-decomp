extern "C" void func_610bec68(char *p)
{
    unsigned *q = *(unsigned **)(p = p + 0x1428);
    ((char *)q)[0x5e65] = 0;
    unsigned *r = *(unsigned **)p;
    *(unsigned *)((char *)r + 0x5e6c) = 0;
}