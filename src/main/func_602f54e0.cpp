struct S {
    char pad[0x28c8];
    int field_28c8;
    int field_28cc;
};

extern "C" void func_602f54e0(S* s) {
    s->field_28c8 = 0;
    s->field_28cc = 0;
}