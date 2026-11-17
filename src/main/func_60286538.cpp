extern "C" int func_600df814(void *, int);

extern "C" int func_60286538(char *a0)
{
    void *p = *(void **)(a0 + 0x13c4);
    char *r = (char *)func_600df814((char *)p + 4, 0);
    unsigned char b = *(unsigned char *)(r + 0x10);
    return (b >> 4) & 1;
}