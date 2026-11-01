struct S_6135a804 {
    unsigned char pad_0[4];
    unsigned char field_4;
    unsigned char field_5;
    unsigned char field_6;
};

extern "C" void func_6135a804(S_6135a804* dst, const S_6135a804* src) {
    dst->field_4 = src->field_4;
    dst->field_5 = src->field_5;
    dst->field_6 = src->field_6;
}