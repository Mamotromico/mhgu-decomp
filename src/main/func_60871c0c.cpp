struct S {
    char pad[0x458];
    float value;
};

extern "C" float func_60871c0c(S* s) {
    return s->value;
}