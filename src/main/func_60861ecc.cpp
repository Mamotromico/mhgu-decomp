struct func_60861ecc_state {
    unsigned char pad0[4];
    volatile unsigned int value_a;
    unsigned char pad1[0x3F8];
    volatile unsigned int value_b;
};

extern "C" void func_60861ecc(struct func_60861ecc_state *state, unsigned int value) {
    state->value_a = value;
    state->value_b = value;
}