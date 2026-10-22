struct Inner {
    unsigned char pad[0x108];
    int value;
};

struct Outer {
    unsigned char pad[0xa4];
    Inner *inner;
};

extern "C" int func_603a9e90(Outer *outer) {
    Inner *inner = outer->inner;
    if (inner)
        return inner->value;
    return 0;
}