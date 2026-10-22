struct Inner {
    unsigned char pad0[0x1bb];
    unsigned char value;
};

struct Outer {
    unsigned char pad0[0x1428];
    Inner* ptr;
};

extern "C" Inner* func_61053100(Outer* outer) {
    Inner* p = outer->ptr;
    p->value = 0;
    return p;
}