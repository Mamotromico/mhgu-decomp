struct func_6063ef00_state {
    unsigned char pad0[0x4c];
    unsigned int flags;
    unsigned char pad1[0x58 - 0x50];
    unsigned int value;
};

extern "C" void func_6063ef00(func_6063ef00_state *state, unsigned int value) {
    state->flags |= 0x4u;
    state->value = value;
}