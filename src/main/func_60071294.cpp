struct Inner {
    char pad0[0x70];
    unsigned int value;
};

struct Outer {
    char pad0[0x75e8];
    Inner *inner;
};

extern "C" unsigned int func_60071294(Outer *outer) {
    return outer->inner->value;
}