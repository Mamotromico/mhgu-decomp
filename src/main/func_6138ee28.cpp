extern "C" int func_6138ee28(void *p)
{
    unsigned char *b = (unsigned char *)p;
    int *f6 = (int *)(b + 0xac);
    if (*f6 != 6)
        return 0;
    int *f98 = (int *)(b + 0x98);
    unsigned x = (unsigned)*f98 - 2u;
    return (x < 3u) ? 1 : 0;
}