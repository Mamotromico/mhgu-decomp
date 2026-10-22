struct S {
    char pad0[4];
    int field_4;
    int field_8;
};

extern "C" void func_60c18560(S *dst, const S *src) {
    dst->field_4 = src->field_4;
    dst->field_8 = src->field_8;
}