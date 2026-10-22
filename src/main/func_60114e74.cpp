extern "C" int func_60114e74(int a, int b)
{
    int (*fn)(int, int) = *(int (**)(int, int))(*(int *)b + 12);
    return fn(b, *(int *)(a + 4));
}