struct func_604d7538_state {
    unsigned char *cursor;
};

extern "C" unsigned char func_604d7538(func_604d7538_state *state)
{
    unsigned char *cursor = state->cursor;
    unsigned char value = *cursor++;
    state->cursor = cursor;
    return value;
}