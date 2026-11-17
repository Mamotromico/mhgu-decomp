extern "C" int func_6056e3b0(void *);

extern "C" void func_605f9a24(char *p)
{
    *(int *)(p + 0x28) = 0xb;
    func_6056e3b0(p);
    *(int *)(p + 0x50) = 1;
}