extern "C" int func_603192f0(void *p)
{
    unsigned char *b = (unsigned char *)p;
    if ((b[0x70] & 1) == 0)
        return 1;
    int v = *(int *)(b + 0x5c);
    int r = 0;
    if (v > 0)
        r = 1;
    return r;
}