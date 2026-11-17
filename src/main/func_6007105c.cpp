struct S {
    char pad[0x75dc];
    int field_75dc;
    int field_75e0;
};

extern "C" int func_6007105c(S *p, int n) {
    if (n >= 1000)
        return p->field_75e0;
    return p->field_75dc;
}