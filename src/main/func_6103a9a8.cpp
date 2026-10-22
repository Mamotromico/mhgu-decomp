struct Inner_6103a9a8 {
    unsigned char pad_0000[0x1bb];
    unsigned char field_01bb;
};

struct Outer_6103a9a8 {
    unsigned char pad_0000[0x1428];
    struct Inner_6103a9a8 *field_1428;
};

extern "C" unsigned int func_6103a9a8(struct Outer_6103a9a8 *a0) {
    return (a0->field_1428->field_01bb >> 3) & 1;
}