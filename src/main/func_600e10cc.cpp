struct S {
    char _pad0[4];
    unsigned char field_4;
};

extern "C" int func_600e10cc(S *s) {
    return s->field_4 & 1;
}