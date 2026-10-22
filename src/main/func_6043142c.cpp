struct S {
    unsigned char pad[4];
    unsigned char field;
};

extern "C" int func_6043142c(S *s) {
    return (unsigned)(s->field - 1) > 1;
}