extern "C" int func_60a26bd8(int, int, int);

extern "C" int func_60a27fc8(int a, int b, int c)
{
    int v = 1;
    if (c != 0)
        v = 3;
    return func_60a26bd8(a, b, v);
}