struct inner_600c0424 {
    unsigned char pad_0x0[0x3a2];
    unsigned char field_0x3a2;
};

struct outer_600c0424 {
    unsigned char pad_0x0[0x1428];
    inner_600c0424 *field_0x1428;
};

extern "C" void func_600c0424(outer_600c0424 *obj) {
    obj->field_0x1428->field_0x3a2 = 0;
}