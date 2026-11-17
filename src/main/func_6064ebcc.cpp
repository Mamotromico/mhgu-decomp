extern "C" void func_606026bc(void *);

struct S {
    char pad0[0x98];
    void (*fn)(void *);
};

extern "C" void func_6064ebcc(void *p)
{
    func_606026bc(p);
    S *s = *(S **)p;
    s->fn(p);
}