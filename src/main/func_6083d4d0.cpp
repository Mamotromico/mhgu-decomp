extern "C" char D_61787fd4[];

struct S {
    void *p;
};

extern "C" void func_6083d4fc(void *);

extern "C" S *func_6083d4d0(S *s)
{
    s->p = D_61787fd4 + 0x8;
    func_6083d4fc(s);
    return s;
}