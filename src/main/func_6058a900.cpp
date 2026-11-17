extern "C" void func_6056e4d8(void *);
extern "C" void func_6058a924(void *);

extern "C" void func_6058a900(char *p)
{
    func_6056e4d8(p);
    func_6058a924(p);
    *(unsigned *)(p + 0x50) = 0;
}