struct inner_60071404 {
    unsigned char pad0[0xb0];
    int field_b0;
};

struct outer_60071404 {
    unsigned char pad0[0x75e8];
    struct inner_60071404 *field_75e8;
};

extern "C" int func_60071404(struct outer_60071404 *obj) {
    return obj->field_75e8->field_b0;
}