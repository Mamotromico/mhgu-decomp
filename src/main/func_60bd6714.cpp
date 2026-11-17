extern "C" void func_60ca65bc(int, int);

extern "C" void func_60bd6714(char *p, int a1)
{
    func_60ca65bc(*(int *)(p + 0xb80), a1);
    func_60ca65bc(*(int *)(p + 0xb84), a1);
}