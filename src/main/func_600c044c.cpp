struct Inner {
    char pad0[0x3a4];
    unsigned char field;
};

struct Outer {
    char pad0[0x1428];
    Inner* inner;
};

extern "C" void func_600c044c(Outer* outer) {
    outer->inner->field = 2;
}