struct sub_600c21b0_inner {
    char pad_0000[0x5C2F];
    unsigned char field_5C2F;
};

struct sub_600c21b0_outer {
    char pad_0000[0x1428];
    sub_600c21b0_inner *field_1428;
};

extern "C" void func_600c21b0(sub_600c21b0_outer *p) {
    p->field_1428->field_5C2F = 0;
}