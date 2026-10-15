struct S {
    char pad[0x13c0];
    unsigned int field;
};

extern "C" unsigned int func_6007270c(S* s) {
    return s->field;
}