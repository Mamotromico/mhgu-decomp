struct Inner {
    unsigned char pad[0x527];
    unsigned char field;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner *ptr;
};

extern "C" int func_60082020(Outer *out, unsigned int mask) {
    return (out->ptr->field & mask) != 0;
}