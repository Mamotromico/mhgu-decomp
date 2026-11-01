struct S {
    char pad[0x3268];
    unsigned int field;
};

extern "C" void func_602ad23c(S *s) {
    unsigned int v = s->field + 1u;
    if (v >= 0x1eu) {
        v = 0x1eu;
    }
    s->field = v;
}