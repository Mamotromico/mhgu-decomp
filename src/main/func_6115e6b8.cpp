struct Inner {
    char pad0[0x4ec];
    int value;
};

struct Outer {
    char pad0[0x3328];
    Inner *inner;
};

extern "C" Inner *func_6115e6b8(Outer *outer) {
    Inner *inner = outer->inner;
    inner->value = -2;
    return inner;
}