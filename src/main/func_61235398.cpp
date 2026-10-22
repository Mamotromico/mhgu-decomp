struct S {
    char pad[0xc];
    int field_c;
    int field_10;
};

extern "C" int func_61235398(S *p) {
    return p->field_c == p->field_10 ? 0 : p->field_c;
}