struct State_605698e8 {
    unsigned char pad0[0xb8];
    volatile unsigned int field_b8;
    unsigned char pad1[0x40];
    volatile unsigned int field_fc;
};

extern "C" void func_605698e8(State_605698e8* s, unsigned int value) {
    s->field_b8 |= 0x100u;
    s->field_fc = value;
}