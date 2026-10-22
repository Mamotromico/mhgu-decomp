struct Inner {
    char pad0[0x54];
    unsigned char value;
};

struct Outer {
    char pad0[0xa4];
    Inner *ptr;
};

extern "C" signed char func_603a3284(Outer *arg) {
    Inner *p = arg->ptr;
    return (signed char)(p ? p->value : 0);
}