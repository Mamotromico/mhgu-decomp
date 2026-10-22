struct Inner_60082004 {
    unsigned char pad0[0x5cde];
    unsigned char value;
};

struct Outer_60082004 {
    unsigned char pad0[0x1428];
    Inner_60082004* inner;
};

extern "C" int func_60082004(Outer_60082004* outer) {
    return outer->inner->value == 1;
}