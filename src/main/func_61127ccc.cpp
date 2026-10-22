struct Inner {
    unsigned char pad0[0x3c8];
    unsigned char field;
};

struct Outer {
    unsigned char pad0[0x3328];
    Inner *inner;
};

extern "C" int func_61127ccc(Outer *o) {
    return (o->inner->field >> 1) & 1;
}