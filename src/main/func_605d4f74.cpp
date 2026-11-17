extern "C" void func_6056e538(char *p, int a, int b);

extern "C" void func_605d4f74(char *p)
{
    int v = *(int *)(p + 0x68);
    func_6056e538(p, v, 3);
    *(int *)(p + 0x4c) = 0;
}