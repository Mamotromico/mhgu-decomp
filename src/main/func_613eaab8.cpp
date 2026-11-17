extern "C" void func_612297ec(void *p);

extern "C" void func_613eaab8(void *p)
{
    void *q = *(void **)((char *)p + 0x8);
    if (q != 0) {
        func_612297ec(q);
        *(unsigned *)((char *)p + 0x8) = 0;
    }
}