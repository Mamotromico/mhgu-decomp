struct Inner {
    unsigned char pad0[0x1c4];
    float value;
};

struct Outer {
    unsigned char pad0[0x1428];
    Inner *inner;
};

extern "C" int func_600c0940(Outer *outer)
{
    return outer->inner->value > 0.0f;
}