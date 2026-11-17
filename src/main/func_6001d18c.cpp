extern "C" void func_6001d1ac(char *a, char *b);

extern "C" void func_6001d18c(char *p)
{
    func_6001d1ac(p, p + 0x1b0);
    func_6001d1ac(p, p + 0x1f0);
}