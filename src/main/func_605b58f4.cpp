extern "C" void func_6056e3b0(void *);
extern "C" void func_605701b0(void *, int);

extern "C" void func_605b58f4(char *p)
{
    *(int *)(p + 0x28) = 0xb;
    func_6056e3b0(p);
    func_605701b0(p, 1);
}