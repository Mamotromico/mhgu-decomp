struct S6028d5b4 {
    char pad[0x26e4];
    int field;
};

extern "C" int func_6028d5b4(S6028d5b4 *p) {
    return p->field == 2;
}