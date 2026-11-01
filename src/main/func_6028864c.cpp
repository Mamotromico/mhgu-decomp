extern "C" int func_6028864c(char *base, int index)
{
    int *p = *(int **)(base + index * 4 + 0x2384);
    if (p == 0)
        return -1;
    return *(int *)((char *)p + 0x1380);
}