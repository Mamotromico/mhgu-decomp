struct S {
    unsigned char pad0[0x4c];
    int field4c;
    unsigned char pad1[0x24];
    unsigned int field74;
};

extern "C" void func_60573464(S* p, int value) {
    p->field74 |= 1u;
    p->field4c = value;
}