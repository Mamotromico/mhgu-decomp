struct func_60573478_s {
    unsigned char pad0[0x50];
    volatile unsigned int field_50;
    unsigned char pad1[0x20];
    volatile unsigned int field_74;
};

extern "C" void func_60573478(func_60573478_s* s, unsigned int v) {
    s->field_74 |= 2u;
    s->field_50 = v;
}