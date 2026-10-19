struct S {
    char pad[0x7c];
    unsigned int field;
};

extern "C" void func_605f83f0(S *s) {
    s->field |= 0x820u;
}