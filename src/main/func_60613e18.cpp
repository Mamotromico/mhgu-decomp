struct Inner_60613e18 {
    unsigned char pad_0x00[0x7c];
    unsigned int field_0x7c;
};

struct Outer_60613e18 {
    unsigned char pad_0x00[0x54];
    struct Inner_60613e18 *field_0x54;
};

extern "C" void func_60613e18(struct Outer_60613e18 *self, unsigned int value)
{
    if (self->field_0x54 != 0)
        self->field_0x54->field_0x7c = value;
}