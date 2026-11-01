struct Inner_600c9a60 {
    unsigned char pad0[0x5ea7];
    signed char field_5ea7;
};

struct Outer_600c9a60 {
    unsigned char pad0[0x1428];
    Inner_600c9a60 *inner_1428;
};

extern "C" int func_600c9a60(Outer_600c9a60 *outer) {
    return outer->inner_1428->field_5ea7 > 0 ? 1 : 0;
}