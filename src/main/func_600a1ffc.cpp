struct Inner_600a1ffc {
    unsigned char pad0[0x5e09];
    unsigned char field_5e09;
};

struct Outer_600a1ffc {
    unsigned char pad0[0x1428];
    Inner_600a1ffc *field_1428;
};

extern "C" void func_600a1ffc(Outer_600a1ffc *self, unsigned char value)
{
    self->field_1428->field_5e09 |= value;
}