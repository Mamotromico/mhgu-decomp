struct Inner {
    unsigned char pad[0x3a2];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner *inner;
};

extern "C" Inner *func_600c0410(Outer *outer) {
    Inner *inner = outer->inner;
    inner->value = 2;
    return inner;
}