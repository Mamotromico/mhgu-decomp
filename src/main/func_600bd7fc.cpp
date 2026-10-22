struct Inner_600bd7fc {
    unsigned char pad[0x5bd];
    unsigned char value;
};

struct Outer_600bd7fc {
    unsigned char pad[0x1428];
    Inner_600bd7fc *inner;
};

extern "C" int func_600bd7fc(Outer_600bd7fc *outer) {
    return outer->inner->value ? 0x80 : 0;
}