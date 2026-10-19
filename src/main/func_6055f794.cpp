struct S_6055f794 {
    unsigned char pad[0x1a4];
    unsigned int field_1a4;
    unsigned int field_1a8;
};

extern "C" void func_6055f794(S_6055f794* p, unsigned int value) {
    unsigned int old = p->field_1a4;
    p->field_1a4 = value;
    p->field_1a8 = old;
}