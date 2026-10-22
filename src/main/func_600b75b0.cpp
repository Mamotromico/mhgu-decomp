struct S {
    unsigned char pad_0[0x73f3];
    unsigned char field_73f3;
    unsigned char pad_73f4[1];
    unsigned char field_73f5;
    unsigned char field_73f6;
};

extern "C" void func_600b75b0(S *s, unsigned char a, unsigned char b, unsigned char c) {
    s->field_73f3 = c;
    s->field_73f5 = a;
    s->field_73f6 = b;
}