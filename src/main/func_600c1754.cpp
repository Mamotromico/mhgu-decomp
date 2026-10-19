struct Inner {
    unsigned char pad[0x1c8];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner* inner;
};

extern "C" unsigned char func_600c1754(Outer* obj) {
    return obj->inner->value;
}