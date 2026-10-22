struct func_605f1290_s {
    unsigned char pad0[0x4c];
    volatile unsigned int field_4c;
    unsigned char pad1[0x04];
    volatile unsigned int field_54;
};

extern "C" void func_605f1290(func_605f1290_s* p, unsigned int value) {
    p->field_54 |= 1u;
    p->field_4c = value;
}