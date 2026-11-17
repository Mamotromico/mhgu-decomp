extern "C" void func_6056e4d8(void);
extern "C" void func_6058eb04(void *);

extern "C" void func_6058eae4(void *p)
{
    func_6056e4d8();
    func_6058eb04(p);
    *(unsigned *)((char *)p + 0x54) = 0;
}