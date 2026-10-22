struct func_613b06f4_state {
    unsigned char pad[0x410];
    unsigned char field_410;
};

extern "C" func_613b06f4_state *func_613b06f4(func_613b06f4_state *state) {
    if (state->field_410 != 0) {
        state->field_410 = 0;
    }
    return state;
}