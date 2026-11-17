extern "C" void *func_60545b78(void *, int, void *);

extern "C" unsigned char *func_6058b43c(void *p, void *q)
{
    unsigned char *r = *(unsigned char **)((char *)p + 0x24);
    return (unsigned char *)func_60545b78(r, 0, q);
}