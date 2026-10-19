struct Inner {
    unsigned char pad[0x36b];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner *inner;
};

extern "C" void func_6007fcbc(Outer *outer) {
    outer->inner->value = 1;
}