extern "C" int func_60283060(void *, int, int);

extern "C" int func_602f54b8(int *p)
{
    int r = func_60283060(p, 0x40, 0x1a);
    if (r == 1)
        return *(unsigned char *)((char *)p + 7);
    return -1;
}