struct S {
    char pad0[0x34];
    unsigned int field34;
    char pad1[0x60 - 0x38];
    unsigned char field60;
};

extern "C" void func_61399354(S* s) {
    if (s->field34 - 1u <= 2u) {
        s->field60 = 1;
    }
}