struct S {
    char pad0[0x448];
    int field448;
    int field44c;
};

extern "C" void func_613cbb34(S* p, int unused, int a, int b) {
    p->field448 = a;
    p->field44c = b;
}