struct inner_61380448 {
    unsigned char pad0[0x6f];
    unsigned char field_6f;
};

struct outer_61380448 {
    unsigned char pad0[0x20];
    struct inner_61380448 *field_20;
};

extern "C" int func_61380448(struct outer_61380448 *obj) {
    struct inner_61380448 *p = obj->field_20;
    if (p == 0)
        return 0;
    return p->field_6f != 0 ? 1 : 0;
}