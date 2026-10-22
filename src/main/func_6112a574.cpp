struct Inner6112a574 {
    char pad_0000[0x3c8];
    unsigned int field_3c8;
};

struct Outer6112a574 {
    char pad_0000[0x3328];
    Inner6112a574 *field_3328;
};

extern "C" Inner6112a574 *func_6112a574(Outer6112a574 *self, unsigned int bits) {
    Inner6112a574 *inner = self->field_3328;
    inner->field_3c8 |= bits;
    return inner;
}