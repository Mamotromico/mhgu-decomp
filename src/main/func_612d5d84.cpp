extern "C" void func_612a5cbc(void *, void *);

extern "C" void func_612d5d84(char *a, void *b)
{
    func_612a5cbc(a + 0x10, b);
    func_612a5cbc(a + 0x70, b);
}