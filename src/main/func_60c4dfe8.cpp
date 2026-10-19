struct S {
    char pad[0xc];
    int field_0xc;
};

extern "C" int func_60c4dfe8(S *p) {
    return p->field_0xc ? 0x100 : 0;
}