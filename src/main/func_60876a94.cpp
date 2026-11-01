struct S {
    char pad[0x70];
    int field;
};

extern "C" int func_60876a94(S* s, int x) {
    return ((x - s->field) >> 2) * 0x3cf3cf3d;
}