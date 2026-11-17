extern "C" void func_612297ec(void *);

struct S {
    char pad[8];
    void *p;
};

extern "C" void func_613eac44(S *s)
{
    if (!s->p)
        return;
    func_612297ec(s->p);
    s->p = 0;
}