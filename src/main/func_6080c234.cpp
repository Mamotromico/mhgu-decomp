struct S {
    char pad0[0x2c];
    void *p2c;
    unsigned size30;
};

extern "C" void func_6080c234(S *s)
{
    void *p = s->p2c;
    unsigned n = s->size30;
    if (p != 0)
        __builtin_memset(p, 0, n);
}