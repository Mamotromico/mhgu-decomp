struct S {
    char pad0[0x10];
    int field_0x10;
    int field_0x14;
    int field_0x18;
};

extern "C" void func_6122bdc4(S* p) {
    p->field_0x10 = 0;
    p->field_0x14 = 0;
    p->field_0x18 = 0;
}