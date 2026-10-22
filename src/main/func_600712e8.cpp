struct Inner {
    unsigned char pad0[0x88];
    void* value;
    unsigned char pad1[0x3a];
    unsigned char flag;
};

struct Outer {
    unsigned char pad[0x75e8];
    Inner* inner;
};

extern "C" void* func_600712e8(Outer* outer) {
    Inner* p = outer->inner;
    return p->flag ? p->value : 0;
}