extern "C" {

struct func_60641a78_state {
    unsigned char pad_0x00[0x4c];
    unsigned int field_0x4c;
    unsigned int field_0x50;
};

void func_60641a78(func_60641a78_state *self, unsigned int value)
{
    self->field_0x50 = value;
    self->field_0x4c |= 1u;
}

}