extern "C" int func_60be854c(char *a, unsigned int i)
{
    int *p;
    if (i > 3)
        return -1;
    p = *(int **)(a + 4 + i * 4);
    if (p != 0)
        return p[1];
    return -1;
}