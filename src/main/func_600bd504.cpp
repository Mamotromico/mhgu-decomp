struct Inner {
    unsigned char pad[0x523];
    unsigned char value;
};

struct Outer {
    unsigned char pad[0x1428];
    Inner* inner;
};

extern "C" Inner* func_600bd504(Outer* outer)
{
    Inner* inner = outer->inner;
    inner->value = 0;
    return inner;
}