extern "C" void func_6009ce40(char *a, int b);

extern "C" void func_600c2768(char *a, int b)
{
    *(int *)(*(char **)(a + 0x1428) + 0x5e38) = b;
    func_6009ce40(a, 0x20);
}