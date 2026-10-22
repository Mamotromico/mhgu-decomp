struct Func60640e84State {
    char pad_0[0x4c];
    unsigned int flags_4c;
    char pad_50[0x10];
    unsigned char value_60;
};

extern "C" void func_60640e84(Func60640e84State* state, unsigned char value) {
    state->flags_4c |= 2u;
    state->value_60 = value;
}