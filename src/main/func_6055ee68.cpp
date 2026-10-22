struct Inner {
    unsigned char pad[0x4c];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x164];
    Inner *inner;
};

extern "C" int func_6055ee68(Outer *outer) {
    Inner *inner = outer->inner;
    if (inner != 0) {
        inner->value = 1;
        return 1;
    }
    return 0;
}