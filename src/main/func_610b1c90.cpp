struct S {
    unsigned char pad[0xcb];
    unsigned char field;
};

extern "C" int func_610b1c90(const S* s) {
    return s->field != 0;
}