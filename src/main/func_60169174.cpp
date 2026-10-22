struct Target {
    unsigned char pad_00[0x30];
    unsigned int field_30;
    unsigned char pad_34[0x26];
    unsigned char field_5a;
};

extern "C" void func_60169174(Target *p, unsigned char value) {
    p->field_30 |= 0x400000u;
    p->field_5a = value;
}