extern "C" int func_60632684(void *p);

extern "C" int func_6063311c(char *p)
{
    int v = *(int *)(p + 0x80);
    if (v == 0)
        return 0;
    return func_60632684((void *)v);
}