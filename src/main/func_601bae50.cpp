struct Data_601bae50 {
    unsigned char pad_0[4];
    int field_4;
    unsigned int field_8;
    unsigned int field_C;
    unsigned char field_10;
    unsigned char pad_11[3];
};

extern "C" void func_601bae50(Data_601bae50 *p) {
    p->field_4 = -1;
    p->field_8 = 0xC47A0000u;
    p->field_C = 0xC47A0000u;
    p->field_10 = 0;
}