extern "C" int func_6018b6d0(void *);

extern "C" int func_6065b4ac(char *p)
{
    int r;
    if (*(int *)(p + 0x4c) != 3)
        return r;
    char *q = *(char **)(p + 0x12c);
    if (q != 0) {
        unsigned char b = *(unsigned char *)(q + 0x16);
        if (b != 0)
            return func_6018b6d0(q);
    }
    return r;
}