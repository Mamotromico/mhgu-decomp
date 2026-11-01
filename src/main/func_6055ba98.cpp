extern "C" int func_6055ba98(char *a, int b, int c)
{
    int *p = *(int **)(a + 0x5c);
    int *q = (int *)((char *)p + (b << 2));
    int v = *(int *)((char *)p + (b << 2));
    if (v == 0)
        return 0;
    int *r = *(int **)v;
    int w = *(int *)((char *)r + (c << 2));
    if (w == 0)
        return 0;
    return 1;
}