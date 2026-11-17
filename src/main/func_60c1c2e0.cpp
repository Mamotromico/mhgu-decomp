extern "C" void *func_60c71b7c(void *, void *);

struct S {
    char pad0[0x18];
    void *field18;
    char pad1[0x44 - 0x18 - 4];
    void *field44;
};

extern "C" void *func_60c1c2e0(S *s)
{
    void *r = func_60c71b7c(s->field18, s->field44);
    return *(void **)r;
}