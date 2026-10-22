struct S {
    unsigned char pad0[4];
    unsigned short field_4;
    unsigned char pad6[0x19];
    unsigned char field_1f;
};

extern "C" unsigned char func_600dcbec(const S *s) {
    return (s->field_4 & 0x1f) == 0x14 ? s->field_1f : 0;
}