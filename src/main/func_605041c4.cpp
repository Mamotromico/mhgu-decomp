struct func_605041c4_state {
    char pad[0x318];
    int values[8];
};

extern "C" void func_605041c4(func_605041c4_state* state, unsigned int index) {
    if (index <= 7U) {
        state->values[index] = 0;
    }
}