struct Inner {
    unsigned char pad[0x5ccb];
    unsigned char field;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner *inner;
};

extern "C" unsigned int func_6009e97c(Outer *outer) {
    return outer->inner->field & 7;
}