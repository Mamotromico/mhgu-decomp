struct Inner {
    unsigned char pad[0x1bb];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner* field;
};

extern "C" unsigned int func_61039060(Outer* self)
{
    return (self->field->value >> 1) & 1u;
}