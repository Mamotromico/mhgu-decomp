extern "C" void func_609dcafc(void *, void *);

struct S {
    char pad0[0x90];
    char f90[0x318 - 0x90];
    void *f318;
    char pad31c[0x130 - 0x31c > 0 ? 0x130 - 0x31c : 0];
};

extern "C" void func_608a64a0(S *s, void *p)
{
    s->f318 = p;
    func_609dcafc((char *)s + 0x90, p);
    func_609dcafc((char *)s + 0x130, p);
}