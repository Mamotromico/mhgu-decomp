struct Inner_6008172c {
    unsigned char pad0[0x518];
    unsigned char field_518;
};

struct Outer_6008172c {
    unsigned char pad0[0x1428];
    Inner_6008172c *ptr_1428;
};

extern "C" int func_6008172c(Outer_6008172c *p) {
    return p->ptr_1428->field_518 == 1;
}