struct S {
    unsigned char pad[0x60];
    unsigned int field_60;
    unsigned int field_64;
    unsigned int field_68;
    unsigned short field_6c;
    unsigned char field_6e;
};

extern "C" void func_61387858(S *p) {
    p->field_60 = 0;
    p->field_64 = 0;
    p->field_68 = 0;
    p->field_6e = 0;
    p->field_6c = 0xffff;
}