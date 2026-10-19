struct Inner_600bc89c {
    unsigned char pad[0x5cbb];
    unsigned char value;
};

struct Outer_600bc89c {
    unsigned char pad[0x1428];
    Inner_600bc89c *inner;
};

extern "C" unsigned char func_600bc89c(Outer_600bc89c *obj) {
    return obj->inner->value;
}