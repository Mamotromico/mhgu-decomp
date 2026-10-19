struct S {
    char pad[0x34];
    int field;
};

extern "C" void func_610b1898(S* s, int value) {
    if (s->field == 0) {
        s->field = value;
    }
}