struct S {
    unsigned char pad0[4];
    int field4;
    int field8;
    int field12;
};

extern "C" void func_6139ed70(S* s) {
    s->field4 = s->field8;
    s->field12 = 0;
}