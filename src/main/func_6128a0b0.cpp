extern "C" void func_612297ec(void *);

struct S {
    char pad0[0x8];
    unsigned *p;
};

extern "C" void func_6128a0b0(S *s)
{
    if (s->p == 0)
        return;
    func_612297ec(s->p);
    s->p = 0;
}