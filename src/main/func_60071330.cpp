struct Inner60071330 {
    char pad_00[0xbf];
    unsigned char field_bf;
};

struct Outer60071330 {
    char pad_00[0x75e8];
    Inner60071330 *field_75e8;
};

extern "C" unsigned char func_60071330(Outer60071330 *self) {
    return self->field_75e8->field_bf;
}