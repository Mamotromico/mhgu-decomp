struct S {
    unsigned int pad0;
    unsigned char f4;
    unsigned char pad5[3];
    unsigned long long f8;
    unsigned short f16;
};

extern "C" void func_612f8b58(S* dst, const S* src) {
    dst->f4 = src->f4;
    dst->f8 = src->f8;
    dst->f16 = src->f16;
}