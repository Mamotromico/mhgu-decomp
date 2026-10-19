struct inner_600bd518 {
    unsigned char pad_0[0x524];
    unsigned char value;
};

struct outer_600bd518 {
    unsigned char pad_0[0x1428];
    inner_600bd518 *inner;
};

extern "C" inner_600bd518 *func_600bd518(outer_600bd518 *arg) {
    inner_600bd518 *p = arg->inner;
    p->value = 1;
    return p;
}