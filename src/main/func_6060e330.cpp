struct S6060e330 {
    unsigned char pad_0[0x5c];
    int field_5c;
    int field_60;
    unsigned char field_64;
};

extern "C" void func_6060e330(S6060e330 *p) {
    p->field_5c = 5;
    p->field_60 = 0;
    p->field_64 = 0;
}