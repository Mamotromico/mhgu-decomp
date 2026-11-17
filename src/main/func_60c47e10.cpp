extern "C" int func_60c47e10(int *a, unsigned b)
{
    int *p = a;
    int r = 0;
    if (b != 0xffffffffu && *(unsigned *)((char *)p + 0xbc) > b) {
        unsigned *tbl = *(unsigned **)((char *)p + 0xc8);
        unsigned v = tbl[b];
        if (v == 0)
            return 0;
        r = *(unsigned char *)((char *)v + 0x5) != 0;
    }
    return r;
}