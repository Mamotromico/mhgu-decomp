struct S {
    char pad[0x68];
    float field_68;
};

extern "C" void func_6095fec8(S *p, float v) {
    p->field_68 = v;
}