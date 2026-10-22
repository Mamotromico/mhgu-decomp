struct Inner_600a1fac {
    unsigned char pad[0x5e08];
    unsigned char value;
};

struct Outer_600a1fac {
    unsigned char pad[0x1428];
    Inner_600a1fac *inner;
};

extern "C" void func_600a1fac(Outer_600a1fac *outer, unsigned int mask) {
    outer->inner->value &= ~mask;
}