struct Func6122f810State {
    unsigned char value;
    unsigned char padding[7];
    int field_8;
};

extern "C" void func_6122f810(Func6122f810State* state, unsigned char value) {
    state->value = value;
    state->field_8 = 3;
}