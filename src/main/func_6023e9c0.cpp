extern "C" void func_60887660(void *);

extern "C" void func_6023e9c0(char *p)
{
    void *q = *(void **)(p + 0x30);
    if (q) {
        func_60887660(q);
        *(unsigned *)(p + 0x30) = 0;
    }
}