struct S {
    char pad[0x75e8];
    char *field;
};

extern "C" char *func_6007135c(S *s) {
    return s->field + 0x98;
}