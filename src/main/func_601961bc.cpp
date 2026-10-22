struct Inner {
    unsigned char pad0[0x64];
    unsigned int value;
};

struct Outer {
    unsigned char pad0[0x30];
    Inner *inner;
};

extern "C" unsigned int func_601961bc(Outer *outer) {
    Inner *inner = outer->inner;
    return inner ? inner->value : 0;
}