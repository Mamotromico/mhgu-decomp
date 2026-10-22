struct Inner {
    char pad0[0x8];
    unsigned int* value;
};

struct Outer {
    char pad0[0x14];
    Inner* inner;
};

extern "C" unsigned int* func_613505b8(Outer* obj) {
    Inner* inner = obj->inner;
    if (inner)
        return inner->value;
    return 0;
}