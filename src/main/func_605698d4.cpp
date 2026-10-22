extern "C" {

struct func_605698d4_state {
    char pad_00[0xb8];
    unsigned int field_b8;
    char pad_bc[4];
    unsigned int field_c0;
};

void func_605698d4(func_605698d4_state *state, unsigned int value)
{
    state->field_b8 |= 0x8;
    state->field_c0 = value;
}

}