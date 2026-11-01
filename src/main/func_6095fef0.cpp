struct Src {
    unsigned int f0;
    unsigned int f4;
    unsigned int f8;
};

struct Dst {
    char pad0[0x90];
    unsigned int f90;
    unsigned int f94;
    unsigned int f98;
    unsigned int f9c;
};

extern "C" void func_6095fef0(Dst *dst, const Src *src)
{
    dst->f90 = src->f0;
    dst->f94 = src->f4;
    dst->f98 = src->f8;
    dst->f9c = 0;
}