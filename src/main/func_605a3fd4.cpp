extern "C" void func_60160720(void *p);
extern "C" void func_60160640(void *p);

extern "C" void func_605a3fd4(char *p)
{
    void *q = *(void **)(p + 0x4c);
    if (q)
    {
        func_60160720(q);
        func_60160640(*(void **)(p + 0x4c));
    }
}