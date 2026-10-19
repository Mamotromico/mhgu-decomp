struct Src_60526544 {
    char pad[0x410];
    volatile unsigned int lo;
    volatile unsigned int hi;
};

struct Dst_60526544 {
    unsigned long long value;
};

extern "C" void func_60526544(Dst_60526544* dst, const Src_60526544* src) {
    unsigned int lo = src->lo;
    unsigned int hi = src->hi;
    dst->value = ((unsigned long long)hi << 32) | lo;
}