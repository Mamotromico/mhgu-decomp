struct S {
    char pad[12];
    unsigned int field;
};

extern "C" void func_6123bc68(S *s, unsigned int value) {
    s->field |= value;
}