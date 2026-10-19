extern "C" {
struct func_60b2ac28_state {
    char pad[0x324];
    unsigned int value;
};

void func_60b2ac28(func_60b2ac28_state* state, unsigned int value) {
    if (state->value < value) {
        state->value = value;
    }
}
}