struct S_601bafa0 {
    unsigned char pad0[4];
    unsigned int field_4;
    unsigned char field_8;
};

extern "C" void func_601bafa0(S_601bafa0* p) {
    p->field_4 = 0x70000;
    p->field_8 = 0;
}