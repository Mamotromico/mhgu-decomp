extern "C" int func_6073939c(int);

extern "C" int func_601c9604(void *p)
{
    int v = *(int *)((char *)p + 0x98);
    if (v == 0)
        return 0;
    return func_6073939c(v);
}