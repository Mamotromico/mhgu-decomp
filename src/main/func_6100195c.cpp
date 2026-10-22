struct Inner6100195c {
    unsigned char pad[0x3b4];
    unsigned short value;
};

struct Outer6100195c {
    unsigned char pad[0x1428];
    Inner6100195c *inner;
};

extern "C" int func_6100195c(Outer6100195c *self) {
    return self->inner->value & 1;
}