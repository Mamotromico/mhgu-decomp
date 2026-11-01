struct func_6123922c_state {
    unsigned char padding_0x00[0x10];
    int field_0x10;
    unsigned char padding_0x14[0x4];
    int field_0x18;
};

extern "C" void func_6123922c(func_6123922c_state *self, int value) {
    self->field_0x10 = self->field_0x10 - value + self->field_0x18;
    self->field_0x18 = value;
}