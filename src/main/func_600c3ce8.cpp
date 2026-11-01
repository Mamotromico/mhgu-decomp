struct inner_600c3ce8 {
    unsigned char pad0[0x24d];
    unsigned char field_24d;
};

struct outer_600c3ce8 {
    unsigned char pad0[0x1428];
    struct inner_600c3ce8 *inner_1428;
};

extern "C" int func_600c3ce8(struct outer_600c3ce8 *ctx, int bit) {
    return (ctx->inner_1428->field_24d & (1 << bit)) != 0;
}