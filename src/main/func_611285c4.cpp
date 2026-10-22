struct sub_611285c4_inner {
    unsigned char pad_0000[0x3c9];
    unsigned char field_03c9;
};

struct sub_611285c4_outer {
    unsigned char pad_0000[0x3328];
    struct sub_611285c4_inner *ptr_3328;
};

extern "C" unsigned int func_611285c4(struct sub_611285c4_outer *a) {
    return (a->ptr_3328->field_03c9 >> 5) & 1u;
}