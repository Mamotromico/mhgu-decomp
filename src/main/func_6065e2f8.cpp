extern "C" unsigned func_6065cb3c(void *p, int mode);

extern "C" unsigned func_6065e2f8(void *p)
{
    unsigned r = func_6065cb3c(p, 3);
    if (r != 0)
        return *(unsigned *)((char *)r + 0x278);
    return 0;
}