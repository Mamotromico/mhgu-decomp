struct Data_60573aa8 {
    unsigned char pad_000[0x64];
    unsigned int value_064;
    unsigned char pad_068[0x0c];
    unsigned int flags_074;
};

extern "C" void func_60573aa8(Data_60573aa8* self, unsigned int value) {
    self->value_064 = value;
    self->flags_074 |= 0xd0u;
}