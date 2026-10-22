struct Src {
    unsigned char f0;
    unsigned char f1;
};

struct Dst {
    unsigned char pad0[0xcac8];
    unsigned char f0;
    unsigned char pad1[0x2b];
    unsigned char f1;
};

extern "C" void func_6006d5b8(Dst *dst, const Src *src) {
    dst->f0 = src->f0;
    dst->f1 = src->f1;
}