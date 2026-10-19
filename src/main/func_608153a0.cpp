struct S {
    char pad[0x24508];
    unsigned char value;
};

extern "C" unsigned char func_608153a0(struct S *s) {
    return s->value;
}