struct S {
    char pad0[0x48];
    unsigned int field_48;
    unsigned int field_4c;
    unsigned short field_50;
};

extern "C" void func_60aecad0(S* s) {
    unsigned int v = s->field_50;
    s->field_48 = v;
    s->field_4c = v;
}