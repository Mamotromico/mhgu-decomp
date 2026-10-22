struct Inner {
    char pad0[0x34];
    int value;
};

struct Outer {
    char pad0[0xa4];
    Inner* inner;
};

extern "C" int func_603a9e7c(Outer* outer) {
    if (outer->inner == 0) {
        return 0;
    }
    return outer->inner->value;
}