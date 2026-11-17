extern "C" void func_60887660(void *p);

extern "C" void func_604ff50c(char *p)
{
    void *q = *(void **)(p + 0x3f8);
    if (q == 0)
        return;
    func_60887660(q);
    *(unsigned *)(p + 0x3f8) = 0;
}