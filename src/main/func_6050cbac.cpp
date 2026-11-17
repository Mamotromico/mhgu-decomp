extern "C" void func_60887660(void *);

struct S {
    char pad0[0x1ac];
    void *p1ac;
};

extern "C" void func_6050cbac(S *s)
{
    if (s->p1ac != 0) {
        func_60887660(s->p1ac);
        s->p1ac = 0;
    }
}