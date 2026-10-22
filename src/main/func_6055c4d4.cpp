struct S {
    char pad[0x45e0];
    unsigned int field_45e0;
    unsigned short field_45e4;
};

extern "C" void func_6055c4d4(S* p) {
    p->field_45e0 = 0;
    p->field_45e4 = 0;
}