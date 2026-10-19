struct Inner {
    unsigned char pad0[0x7c];
    void *value;
};

struct Outer {
    unsigned char pad0[0x75e8];
    struct Inner *inner;
};

extern "C" void *func_600713a4(struct Outer *o)
{
    return o->inner->value;
}