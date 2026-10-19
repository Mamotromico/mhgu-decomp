struct S_600debbc {
    unsigned char pad_0[4];
    int field_4;
    short field_8;
    unsigned char field_a;
    unsigned char pad_b[1];
};

extern "C" void func_600debbc(S_600debbc *p) {
    p->field_a = 0;
    p->field_8 = 0;
    p->field_4 = 0;
}