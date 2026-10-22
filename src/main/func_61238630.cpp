struct Inner {
    unsigned char pad0[0x10];
    unsigned int value;
};

struct Outer {
    unsigned char pad0[0x8];
    Inner *inner;
    unsigned char pad1[0x8];
    unsigned int result;
};

extern "C" void func_61238630(Outer *p) {
    p->result = p->inner->value << 3;
}