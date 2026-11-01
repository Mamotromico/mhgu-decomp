extern "C" int func_60b6b9c0(char *p, unsigned idx)
{
    char *q = *(char **)(p + 0xa4);
    if (!q)
        return 0;
    if (!*(int *)(p + 0x68))
        return 0;
    return (int)(q + (idx << 7));
}