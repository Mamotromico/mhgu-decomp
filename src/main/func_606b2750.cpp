extern "C" void func_6056e4d8(void);
extern "C" void func_606b2770(void *p);

extern "C" void func_606b2750(void *p)
{
    func_6056e4d8();
    func_606b2770(p);
    *(unsigned *)((char *)p + 0x4c) = 0;
}