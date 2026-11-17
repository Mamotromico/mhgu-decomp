extern "C" int func_603a9f54(char *obj, int sel)
{
    unsigned *p = *(unsigned **)(obj + 0xa4);
    int r = 0;
    if (p == 0)
        return r;
    if (sel == 0)
        return *(int *)((char *)p + 0x4c);
    if (sel == 1)
        return *(int *)((char *)p + 0x50);
    return r;
}