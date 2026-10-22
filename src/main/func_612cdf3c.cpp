struct S {
    char pad0[4];
    unsigned char field4;
    char pad5[3];
    int field8;
};

extern "C" void func_612cdf3c(S* dst, const S* src) {
    dst->field4 = src->field4;
    dst->field8 = src->field8;
}