extern "C" void func_60602334(void *);

struct S {
    char pad_0[0x64];
    void (*fn)(void *);
};

extern "C" void func_60602a54(S *s)
{
    func_60602334(s);
    S *t = *(S **)s;
    t->fn(s);
}