struct S {
    char pad[0x35e4];
    unsigned int field;
};

extern "C" unsigned int func_60523974(S* s) {
    return s->field & 1u;
}