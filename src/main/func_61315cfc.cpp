struct S {
    char pad[0x84];
    int value;
};

extern "C" int func_61315cfc(S* s) {
    return s->value == 1;
}