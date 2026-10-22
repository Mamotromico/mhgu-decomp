struct func_604ee8ac_S {
    unsigned char pad_0[0x1a18];
    volatile int field_1a18;
    volatile unsigned char field_1a1c;
};

extern "C" void func_604ee8ac(func_604ee8ac_S* p, int v) {
    p->field_1a1c = 1;
    p->field_1a18 = v;
}