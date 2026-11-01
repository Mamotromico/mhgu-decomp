struct S {
    unsigned char pad0[0xac];
    int field_ac;
    int field_b0;
    unsigned char pad1[0x0c];
    int field_c0;
    unsigned char pad2[0x1c];
    unsigned char field_e0;
    unsigned char pad3[2];
    unsigned char field_e3;
};

extern "C" void func_60b2a704(volatile S *s, int val) {
    s->field_b0 = val;
    s->field_ac = 0;
    s->field_e0 = 1;
    s->field_e3 = 0;
    s->field_c0 = 0;
}