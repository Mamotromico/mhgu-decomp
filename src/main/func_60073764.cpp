struct S {
    char pad[0x10];
    unsigned int field_0x10;
};

extern "C" void func_60073764(S* p) {
    p->field_0x10 |= 0xc;
}