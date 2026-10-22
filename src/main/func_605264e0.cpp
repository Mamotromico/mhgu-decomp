struct S {
    unsigned char pad[0x40c];
    unsigned char field;
};

extern "C" int func_605264e0(const S* s) {
    return s->field != 0xff ? 1 : 0;
}