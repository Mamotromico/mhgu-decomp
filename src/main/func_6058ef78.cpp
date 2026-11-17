extern "C" void func_6056e4d8(void *);
extern "C" void func_6058ef9c(void *);

extern "C" void func_6058ef78(void *p)
{
    func_6056e4d8(p);
    func_6058ef9c(p);
    *(unsigned *)((char *)p + 0x50) = 0;
}