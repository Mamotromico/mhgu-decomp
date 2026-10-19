struct S {
    char pad[0x1c];
    int value;
};

extern "C" int func_603f8690(const S* s) {
    int value = s->value;
    return value == 1 ? value : 0;
}