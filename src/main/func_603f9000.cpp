struct S603f9000 {
    unsigned char pad0[0xa0];
    unsigned short field_a0;
    unsigned char field_a2;
};

extern "C" void func_603f9000(S603f9000 *p) {
    p->field_a0 = 0;
    p->field_a2 = 0;
}