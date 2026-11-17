extern "C" int func_6048aa10(int);

extern "C" int func_604a21f8(char *p)
{
    int v = *(int *)(p + 0x1384);
    if (v == 0)
        return 0;
    return func_6048aa10(v);
}