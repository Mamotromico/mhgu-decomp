struct S {
    unsigned char pad[12];
    unsigned char b;
};

extern "C" int func_6121b484(S *s) {
    return s->b == 0;
}