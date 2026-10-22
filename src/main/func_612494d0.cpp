struct Dest {
    unsigned char pad[0xc4];
    unsigned int field_c4;
    unsigned int field_c8;
    unsigned int field_cc;
};

extern "C" void func_612494d0(Dest *dst, unsigned int val, unsigned long long *src) {
    dst->field_c4 = val;
    unsigned long long v = *src;
    dst->field_cc = (unsigned int)(v >> 32);
    dst->field_c8 = (unsigned int)v;
}