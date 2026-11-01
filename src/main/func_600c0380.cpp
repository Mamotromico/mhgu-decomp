struct Inner {
    char pad0[0x5de8];
    int value;
};

struct Outer {
    char pad0[0x1428];
    struct Inner *inner;
};

extern "C" int func_600c0380(struct Outer *o)
{
    int value = o->inner->value;
    int result = 0;
    if (value > 0)
        result = 1;
    return result;
}