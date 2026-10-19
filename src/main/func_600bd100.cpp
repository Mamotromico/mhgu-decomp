struct Inner {
    unsigned char pad[0x520];
    unsigned char field;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner *inner;
};

extern "C" void func_600bd100(Outer *outer) {
    outer->inner->field = 1;
}