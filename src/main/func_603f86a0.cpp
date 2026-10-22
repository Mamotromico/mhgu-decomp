struct S {
    char pad[0x1c];
    int field;
};

extern "C" int func_603f86a0(S* s) {
    return s->field == 9;
}