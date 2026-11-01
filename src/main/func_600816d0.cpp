struct inner_600816d0 {
    unsigned char pad_0[0x505];
    unsigned char field_505;
};

struct outer_600816d0 {
    unsigned char pad_0[0x1428];
    struct inner_600816d0 *inner;
};

extern "C" int func_600816d0(struct outer_600816d0 *p)
{
    return (p->inner->field_505 & 0xFE) == 2;
}