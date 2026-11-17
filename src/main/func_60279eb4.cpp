extern "C" void *func_6027a014(void *);

struct S {
    char pad[0x60];
    unsigned short h;
};

extern "C" void func_60279eb4(S *s, unsigned v)
{
    s->h = (unsigned short)v;
    char *p = (char *)func_6027a014(s);
    if (p != 0)
        *(unsigned *)(p + 0x14a0) = v;
}