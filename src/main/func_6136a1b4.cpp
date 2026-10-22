struct S {
    int field_0;
    char *field_4;
    int field_8;
};

extern "C" void func_6136a1b4(S *s) {
    s->field_4[s->field_8 - 1] = 0;
}