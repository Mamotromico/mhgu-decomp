struct S {
    char pad0[0x4c];
    unsigned int flags;
    char pad1[0x08];
    int field58;
    int field5c;
};

extern "C" void func_606b84cc(S* p, int a, int b) {
    p->flags |= 0x20;
    p->field58 = a;
    p->field5c = b;
}