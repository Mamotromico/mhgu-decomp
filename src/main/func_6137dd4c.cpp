struct S {
    char pad[0x84];
    int field_84;
    int field_88;
};

extern "C" void func_6137dd4c(S* s) {
    s->field_84 = 0;
    s->field_88 = 0;
}