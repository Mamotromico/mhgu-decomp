extern "C" void func_60887660(void *);

extern "C" void func_603d7318(char *p)
{
    void *x = *(void **)(p + 0x8d0);
    if (x == 0)
        return;
    func_60887660(x);
    *(unsigned *)(p + 0x8d0) = 0;
}