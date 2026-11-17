extern "C" void func_6081fbd4(unsigned *dst, unsigned *src, int n);

extern "C" void func_612cf830(unsigned *dst, unsigned *src)
{
    if ((unsigned *)((char *)dst + 0x6c) == src)
        return;
    unsigned a = *(unsigned *)((char *)src + 0);
    unsigned b = *(unsigned *)((char *)src + 4);
    func_6081fbd4((unsigned *)((char *)dst + 0x6c), (unsigned *)a, (int)b);
}