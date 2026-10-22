struct Func6063fd78Data {
    unsigned char pad_00[0x4c];
    unsigned int field_4c;
    unsigned char pad_50[0x12];
    unsigned char field_62;
};

extern "C" void func_6063fd78(Func6063fd78Data *p, unsigned char value) {
    p->field_4c |= 0x40u;
    p->field_62 = value;
}