struct S {
    char pad0[4];
    unsigned char b4;
    unsigned char b5;
    unsigned char b6;
    unsigned char b7;
    unsigned char b8;
    unsigned char b9;
    unsigned char b10;
    unsigned char b11;
    unsigned char b12;
    unsigned char b13;
    unsigned char b14;
    unsigned char b15;
};

extern "C" void func_604d399c(S *dst, const S *src) {
    if (!src) return;
    dst->b4 = src->b4;
    dst->b5 = src->b5;
    dst->b6 = src->b6;
    dst->b7 = src->b7;
    dst->b8 = src->b8;
    dst->b9 = src->b9;
    dst->b10 = src->b10;
    dst->b11 = src->b11;
    dst->b12 = src->b12;
    dst->b13 = src->b13;
    dst->b14 = src->b14;
    dst->b15 = src->b15;
}