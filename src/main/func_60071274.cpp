struct Inner {
    char pad[0x6b];
    unsigned char value;
};

struct Outer {
    char pad[0x75e8];
    Inner *inner;
};

extern "C" unsigned char func_60071274(Outer *outer) {
    return outer->inner->value;
}