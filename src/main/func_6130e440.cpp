struct Data_6130e440 {
    unsigned char pad_0x0[0xc];
    unsigned int field_0xc;
    unsigned char pad_0x10[0x5d8 - 0x10];
    unsigned int field_0x5d8;
};

extern "C" void func_6130e440(Data_6130e440 *self, unsigned int value) {
    self->field_0xc = value;
    self->field_0x5d8 |= 1u;
}