struct Inner {
    unsigned char pad0[0x521];
    unsigned char value;
};

struct Outer {
    unsigned char pad0[0x1428];
    Inner *inner;
};

extern "C" Inner *func_600bd114(Outer *outer)
{
    Inner *inner = outer->inner;
    inner->value = 2;
    return inner;
}