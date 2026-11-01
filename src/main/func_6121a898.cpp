struct S {
    int field_0;
    unsigned char field_4;
    unsigned char pad_5[3];
    int field_8;
    unsigned char field_c;
    unsigned char pad_d[3];
    int field_10;
};

extern "C" void func_6121a898(volatile S *s, int value) {
    s->field_0 = value;
    s->field_c = 0;
    s->field_4 = 0;
    s->field_10 = 0;
    s->field_8 = -1;
}