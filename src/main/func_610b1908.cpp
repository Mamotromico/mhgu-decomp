extern "C" void func_600c1660(void *);

struct S {
    char pad[0x34];
    void *field_0x34;
};

extern "C" void func_610b1908(S *s) {
    void *p = s->field_0x34;
    if (p == 0)
        return;
    func_600c1660(p);
}