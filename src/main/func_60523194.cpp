extern "C" void func_60523194(char *p, int a)
{
    int v = *(int *)(p + 0x2c) + a;
    if (v > 0x98967f)
        v = 0x98967f;
    if (v <= 0)
        v = 0;
    *(int *)(p + 0x2c) = v;
}