extern "C" void func_6056e528(void *, int, int);

extern "C" void func_60613d34(unsigned char *p, int b, int c)
{
    *(unsigned char *)(p + 0x4c) = (unsigned char)b;
    func_6056e528(p, 0x38, b);
}