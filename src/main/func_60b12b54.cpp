extern "C" int func_60b12b54(char *p)
{
    char *q = *(char **)(p + 0x78);
    if (q == 0)
        return 0;
    if (*(int *)(q + 0x10) != 0)
        return 1;
    return *(int *)(q + 0x14) != 0;
}