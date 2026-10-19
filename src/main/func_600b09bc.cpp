struct S_600b09bc {
    char pad[0x50c];
    float field;
};

extern "C" float func_600b09bc(S_600b09bc* s) {
    return s->field;
}