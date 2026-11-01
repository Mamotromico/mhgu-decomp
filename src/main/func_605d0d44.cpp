struct func_605d0d44_state {
    unsigned char pad0[0x50];
    unsigned int field_0x50;
    unsigned int field_0x54;
    unsigned char pad_0x58[0x14];
    unsigned char field_0x6c;
};

extern "C" void func_605d0d44(func_605d0d44_state* state, unsigned int value) {
    state->field_0x50 |= 2u;
    state->field_0x54 = value;
    state->field_0x6c = 1u;
}