struct S {
    int field_0;
    unsigned short field_4;
};

extern "C" void func_6130ca20(S* dst, const S* src) {
    dst->field_0 = src->field_0;
    dst->field_4 = src->field_4;
}