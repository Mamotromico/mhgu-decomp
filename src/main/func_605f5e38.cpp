struct func_605f5e38_layout {
    unsigned char pad_00[0x4c];
    volatile unsigned int field_4c;
    unsigned char pad_50[0x94];
    volatile unsigned char field_e4;
    volatile unsigned char field_e5;
};

extern "C" void func_605f5e38(func_605f5e38_layout *self, unsigned int value)
{
    self->field_4c = value;
    self->field_e4 = 0;
    self->field_e5 = 0;
}