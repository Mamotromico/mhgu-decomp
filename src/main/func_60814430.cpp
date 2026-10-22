struct S {
    unsigned char pad[0x2c8d8];
    int value;
};

extern "C" int func_60814430(S* s) {
    return s->value != 0;
}