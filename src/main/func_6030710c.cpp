struct S6030710c {
    unsigned char pad0[0x13b0];
    int field13b0;
    unsigned char pad1[0x4];
    int field13b8;
};

extern "C" void func_6030710c(S6030710c* p, int a, int b) {
    p->field13b0 = a;
    p->field13b8 = b;
}