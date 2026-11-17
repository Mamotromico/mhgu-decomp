extern "C" void func_605c55b0(void *);

extern "C" void func_6063a3e8(void *p)
{
    void *q = *(void **)((char *)p + 0xa4);
    if (q)
        func_605c55b0(q);
}