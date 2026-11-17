extern "C" void func_60545bcc(unsigned, unsigned, unsigned);

extern "C" void func_60630ea0(unsigned char *p, unsigned arg1)
{
    unsigned a = *(unsigned *)(p + 0x24);
    func_60545bcc(a, 0x21, arg1);
}