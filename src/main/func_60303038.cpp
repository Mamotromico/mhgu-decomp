struct Func60303038State {
    char pad[0x2b0c];
    float field;
};

extern "C" void func_60303038(Func60303038State *state, float value) {
    if (state->field < value) {
        state->field = value;
    }
}