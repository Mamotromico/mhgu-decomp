struct S {
    char pad0[0xd6c];
    unsigned int field_d6c;
    char pad1[4];
    unsigned int field_d74;
};

extern "C" void func_60524580(S *p) {
    p->field_d6c |= p->field_d74;
}