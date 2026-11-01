extern "C" int func_6065b47c(char *p);

extern "C" int func_6065b47c(char *p)
{
    if (*(int *)(p + 0x4c) != 3)
        return 0;
    char *q = *(char **)(p + 0x12c);
    if (q == 0)
        return 0;
    if (*(unsigned char *)(q + 0x16) != 0)
        return 1;
    return 0;
}