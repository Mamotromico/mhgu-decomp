extern "C" void func_6056e4d8(void);
extern "C" void func_605d07fc(void *p);

extern "C" void func_605d07dc(char *p)
{
    func_6056e4d8();
    func_605d07fc(p);
    *(unsigned *)(p + 0x50) = 0;
}