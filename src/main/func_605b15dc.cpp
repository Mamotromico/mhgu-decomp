struct S {
    char pad[0x58];
    unsigned char field;
};

extern "C" int func_605b15dc(const struct S *s) {
    int result = 0;
    if (s->field == 2) {
        result = 1;
    }
    return result;
}