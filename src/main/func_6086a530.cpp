struct S {
    char pad0[0x4];
    int f4;
    char pad8[0x4];
    int fc;
    int f10;
    int f14;
};

extern "C" void func_6086a530(S* dst, const S* src) {
    dst->f4 = src->f4;
    dst->fc = src->fc;
    dst->f10 = src->f10;
    dst->f14 = src->f14;
}