struct S {
    char pad[0x70];
    void *a;
    void *b;
};

extern "C" void func_605c9fe0(struct S *s, void *a, void *b)
{
    if (a == 0)
        return;
    if (b == 0)
        return;
    s->a = a;
    s->b = b;
}