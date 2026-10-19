struct S {
    char padding[0xa4];
    unsigned int field;
};

extern "C" void func_605f33f8(S *s) {
    s->field |= 3u;
}