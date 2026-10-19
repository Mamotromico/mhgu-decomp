struct Inner {
    unsigned char pad[0x5d3];
    unsigned char field;
};

struct Outer {
    unsigned char pad[0x3328];
    Inner *inner;
};

extern "C" void func_61128748(Outer *outer, unsigned char value) {
    outer->inner->field = value;
}