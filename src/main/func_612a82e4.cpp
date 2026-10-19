struct S {
    char pad[0x40];
    unsigned int field;
};

extern "C" void func_612a82e4(S* s, unsigned int value) {
    s->field |= value;
}