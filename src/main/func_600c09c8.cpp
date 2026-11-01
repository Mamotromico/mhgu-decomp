struct Dest {
    unsigned int f0;
    unsigned int f4;
    unsigned int f8;
    unsigned int fc;
};

struct Src {
    unsigned char pad0[0x40];
    unsigned int f40;
    unsigned int f44;
    unsigned int f48;
};

extern "C" void func_600c09c8(Dest *dst, const Src *src) {
    dst->f0 = src->f40;
    dst->f4 = src->f44;
    dst->f8 = src->f48;
    dst->fc = 0;
}