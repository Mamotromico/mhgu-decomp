struct S {
    char pad[0x3dc];
    unsigned char field;
};

extern "C" int func_605102f8(S* s) {
    return (s->field & 0x18) == 0;
}