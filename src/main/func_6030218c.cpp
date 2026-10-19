struct S {
    unsigned char pad[0x2843];
    unsigned char field;
};

extern "C" unsigned int func_6030218c(const struct S* s) {
    return (s->field >> 4) & 1;
}