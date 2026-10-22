struct S {
    unsigned char pad[4];
    unsigned char field;
};

extern "C" int func_600e10d8(S *s) {
    return (s->field & 5) == 5;
}