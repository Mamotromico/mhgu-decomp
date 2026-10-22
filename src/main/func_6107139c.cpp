struct Inner {
    char pad0[0x1bb];
    unsigned char flags;
};

struct Outer {
    char pad0[0x1428];
    struct Inner *inner;
};

extern "C" unsigned int func_6107139c(struct Outer *obj)
{
    return (obj->inner->flags >> 4) & 1u;
}