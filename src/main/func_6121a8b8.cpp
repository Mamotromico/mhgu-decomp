struct S {
    unsigned char pad0[4];
    unsigned char field_4;
    unsigned char pad5[3];
    int field_8;
    unsigned char field_c;
    unsigned char pad_d[3];
    int field_10;
};

extern "C" void func_6121a8b8(S *p, unsigned char value, int value2) {
    p->field_c = value;
    p->field_4 = 0;
    p->field_10 = 0;
    p->field_8 = value2;
}