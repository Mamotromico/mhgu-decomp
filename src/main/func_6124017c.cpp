struct S {
    char pad[0xc];
    unsigned int field_c;
    unsigned int field_10;
};

extern "C" unsigned int func_6124017c(struct S *s) {
    unsigned int a = s->field_c;
    if (a == s->field_10)
        a = 0;
    return a;
}