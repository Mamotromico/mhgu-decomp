struct S {
    char pad[0x258];
    int field;
};

extern "C" int func_6133d270(S *s) {
    int v = s->field;
    if (v != 0)
        v = 4;
    return v;
}