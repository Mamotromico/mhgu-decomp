extern "C" void func_60887660(void *);

struct S {
    char pad[0xb4];
    void *p;
};

extern "C" void func_603b1940(S *s)
{
    if (s->p != 0) {
        func_60887660(s->p);
        s->p = 0;
    }
}