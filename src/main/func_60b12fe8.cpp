struct State {
    char pad0[8];
    unsigned int field_8;
    unsigned char field_c;
};

extern "C" void func_60b12fe8(State* state, unsigned int value) {
    unsigned int shifted = 1;
    if (value < 0x21) {
        shifted <<= value;
    }
    state->field_8 = shifted;
    state->field_c = (unsigned char)value;
}