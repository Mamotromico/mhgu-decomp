struct Inner {
    char pad0[0x3a8];
    unsigned int flags;
};

struct Outer {
    char pad1[0x1428];
    struct Inner *inner;
};

extern "C" void func_6009ce28(struct Outer *outer, unsigned int bits)
{
    outer->inner->flags |= bits;
}