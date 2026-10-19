struct Inner {
    unsigned char pad[0x5c8d];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner* inner;
};

extern "C" void func_600bd674(Outer* p, unsigned char v) {
    p->inner->value = v;
}