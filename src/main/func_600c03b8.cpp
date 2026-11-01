struct inner_600c03b8 {
    unsigned char pad_00[0x5dec];
    int value;
};

struct outer_600c03b8 {
    unsigned char pad_00[0x1428];
    inner_600c03b8 *ptr;
};

extern "C" int func_600c03b8(outer_600c03b8 *arg) {
    return arg->ptr->value > 0;
}