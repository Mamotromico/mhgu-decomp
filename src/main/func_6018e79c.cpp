struct S {
    unsigned char pad[8];
    unsigned int field;
};

extern "C" int func_6018e79c(struct S *s) {
    unsigned int v = s->field;
    int result = 0;
    if (v - 0x5e < 4)
        result = 1;
    return result;
}