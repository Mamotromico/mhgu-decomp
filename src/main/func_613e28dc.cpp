struct S {
    char pad_0[0x1c];
    int field_1c;
    int field_20;
    char pad_24[0xc];
    int field_30;
};

extern "C" void func_613e28dc(S* s) {
    s->field_30 = 0;
    s->field_1c = 0;
    s->field_20 = 0;
}