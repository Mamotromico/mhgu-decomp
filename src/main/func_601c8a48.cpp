struct Data_601c8a48 {
    unsigned char pad0[0x98];
    int field_98;
    unsigned char pad1[0xac - 0x9c];
    unsigned char field_ac;
    unsigned char pad2[0xb0 - 0xad];
    int field_b0;
};

extern "C" void func_601c8a48(Data_601c8a48 *self) {
    self->field_98 = 0;
    self->field_ac = 0;
    self->field_b0 = 0;
}