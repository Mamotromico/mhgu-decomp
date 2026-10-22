struct S {
    unsigned char pad[8];
    unsigned int value;
};

extern "C" int func_6018e83c(const struct S *s) {
    return (unsigned int)(s->value - 0xf7u) < 0xcu;
}