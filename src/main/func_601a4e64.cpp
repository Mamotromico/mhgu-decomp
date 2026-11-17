extern "C" void func_603df2a8(void *dst, const void *src, unsigned n);

extern "C" void func_601a4e64(char *a, char *src)
{
    char *d = a + 0x110;
    func_603df2a8(src, d - 8, 0x28);
}