struct inner_603a340c {
    unsigned char padding[0x10c];
    unsigned char value;
};

struct outer_603a340c {
    unsigned char padding[0xa4];
    inner_603a340c *inner;
};

extern "C" unsigned int func_603a340c(outer_603a340c *p) {
    inner_603a340c *inner = p->inner;
    if (inner == 0) {
        return 0;
    }
    return (unsigned int)(inner->value >> 7);
}