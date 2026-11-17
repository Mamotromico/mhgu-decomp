extern "C" void func_605c5500(void *, unsigned, unsigned);

struct S {
    char pad0[0x9c];
    unsigned f9c;
    char pad1[0xb4 - 0x9c - 4];
    unsigned fb4;
};

extern "C" void func_605c4108(S *s, unsigned a, unsigned b)
{
    s->f9c = a;
    unsigned v = s->fb4;
    if (v == 0)
        return;
    func_605c5500((void *)v, b, b);
}