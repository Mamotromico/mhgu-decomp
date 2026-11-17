extern "C" void func_612297ec(void *);

struct S {
    char pad0[0x8];
    void *p;
};

extern "C" void func_613ea918(S *s)
{
    void *p = s->p;
    if (p == 0)
        return;
    func_612297ec(p);
    s->p = 0;
}