struct S_6018a3ec {
    unsigned char pad0[0xa8];
    unsigned char field_a8;
    unsigned char pad1[3];
    unsigned int field_ac;
    unsigned int field_b0;
};

extern "C" void func_6018a3ec(S_6018a3ec* p) {
    p->field_a8 = 0;
    p->field_ac = 0xffffffffu;
    p->field_b0 = 0;
}