struct S {
    char pad[0x38];
    unsigned int field;
};

extern "C" void func_610b18a8(S* s, unsigned int value) {
    if (s->field == 0) {
        s->field = value;
    }
}