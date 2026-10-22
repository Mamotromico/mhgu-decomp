struct Inner {
    unsigned char pad0[0x104];
    unsigned int value0;
    unsigned int value1;
};

struct Outer {
    unsigned char pad0[0x8];
    Inner *inner;
    unsigned char pad1[0x8c];
    unsigned int value0;
    unsigned int value1;
};

extern "C" void func_60aecb30(Outer *outer) {
    Inner *inner = outer->inner;
    outer->value0 = inner->value0;
    outer->value1 = inner->value1;
}