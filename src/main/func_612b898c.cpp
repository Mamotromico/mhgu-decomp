extern "C" int func_612a9638(int);

extern "C" int func_612b898c(char *p)
{
    int v = *(int *)(p + 0x84);
    if (v == 0)
        return 0;
    return func_612a9638(v);
}