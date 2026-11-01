struct S {
    unsigned char pad0[4];
    unsigned char field4;
    unsigned char pad5;
    unsigned short field6;
    unsigned char field8;
};

extern "C" void func_612f8a64(S *dst, const S *src) {
    dst->field4 = src->field4;
    dst->field6 = src->field6;
    dst->field8 = src->field8;
}