struct S {
    unsigned char pad[0x25];
    unsigned char field;
};

extern "C" int func_6130f72c(S *s) {
    return (s->field & 3) == 2;
}