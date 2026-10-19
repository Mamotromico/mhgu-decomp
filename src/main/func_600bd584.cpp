struct Inner {
    unsigned char pad[0x525];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner *inner;
};

extern "C" void func_600bd584(Outer *outer) {
    outer->inner->value = 0;
}