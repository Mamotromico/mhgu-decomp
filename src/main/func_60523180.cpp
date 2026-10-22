struct S {
    unsigned char pad[0x24];
    int field;
};

extern "C" int func_60523180(const S* s, int value) {
    return s->field >= value;
}