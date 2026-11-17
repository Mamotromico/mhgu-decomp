extern "C" void func_60545bcc(unsigned, unsigned, unsigned);

extern "C" void func_605c561c(char *p, unsigned arg)
{
    unsigned a = *(unsigned *)(p + 0x24);
    unsigned b = *(unsigned *)(p + 0x68);
    func_60545bcc(a, b, arg);
}