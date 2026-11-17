extern "C" int func_60887648(int);

extern "C" int func_600709c0(char *p, int v)
{
    *(int *)(p + 0x75dc) = v;
    return func_60887648(v);
}