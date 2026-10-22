struct Inner {
    unsigned char pad0[0x5e08];
    unsigned char value;
};

struct Outer {
    unsigned char pad0[0x1428];
    Inner *inner;
};

extern "C" void func_600a1f94(Outer *arg) {
    arg->inner->value = 0;
}