struct S {
    char pad0[8];
    int field8;
    int field12;
    unsigned char field16;
};

extern "C" void func_6139493c(S* s) {
    s->field8 = 0;
    s->field12 = 0;
    s->field16 = 0;
}