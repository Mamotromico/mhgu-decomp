struct S {
    char pad[0x69c];
    int value;
};

extern "C" int func_60677858(S *s) {
    int value = s->value;
    return value == 1 ? value : 0;
}