struct Layout {
    unsigned char pad0[0x50];
    unsigned int field_50;
    unsigned char pad54[0x08];
    unsigned int field_5c;
};

extern "C" void func_606b58d4(Layout* p, unsigned int value) {
    p->field_50 |= 0x80u;
    p->field_5c = value;
}