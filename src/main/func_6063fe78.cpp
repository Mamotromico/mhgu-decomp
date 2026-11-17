extern "C" void func_6056e3b0(void *);

extern "C" void func_6063fe78(void *p)
{
    *(unsigned *)((char *)p + 0x28) = 0x25;
    func_6056e3b0(p);
    *(unsigned *)((char *)p + 0x4c) = 1;
}