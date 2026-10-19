struct Inner {
    unsigned char pad[0x526];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner* inner;
};

extern "C" void func_600bd598(Outer* p) {
    p->inner->value = 0;
}