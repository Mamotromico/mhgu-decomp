extern "C" int func_6133cfb0(char *p, int v)
{
    int *q = *(int **)(p + 0x258);
    if (!q)
        return 0;
    if (q[0x8 / 4] == v)
        return 1;
    if (q[0x438 / 4] == v)
        return 1;
    if (q[0x868 / 4] == v)
        return 1;
    if (q[0xc98 / 4] == v)
        return 1;
    return 0;
}