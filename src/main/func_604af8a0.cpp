extern "C" void func_604ad0e8(void *);

extern "C" void func_604af8a0(void *p)
{
    *(unsigned *)((char *)p + 0x3c) = 4;
    func_604ad0e8(p);
}