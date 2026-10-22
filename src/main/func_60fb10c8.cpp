struct Inner {
    char pad0[0x1bb];
    unsigned char flag;
};

struct Outer {
    char pad0[0x1428];
    Inner* inner;
};

extern "C" int func_60fb10c8(Outer* o) {
    return o->inner->flag != 0;
}