struct S {
    int field_0;
    int field_4;
    unsigned char field_8;
    unsigned char pad_9[0x103];
    int field_10c;
};

extern "C" void func_6086e49c(S *p) {
    p->field_0 = 0;
    p->field_4 = 0;
    p->field_8 = 1;
    p->field_10c = -1;
}