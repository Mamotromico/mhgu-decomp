struct Inner_61069828 {
    unsigned char pad_0[0x3bc];
    unsigned char value;
};

struct Outer_61069828 {
    unsigned char pad_0[0x1428];
    Inner_61069828 *inner;
};

extern "C" int func_61069828(Outer_61069828 *outer) {
    return outer->inner->value == 3;
}