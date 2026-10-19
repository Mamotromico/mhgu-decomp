struct Inner {
    char pad_00[0x58];
    int value;
};

struct Outer {
    char pad_00[0x98];
    Inner *inner;
};

extern "C" void func_605c5b2c(Outer *outer, int value)
{
    Inner *inner = outer->inner;
    if (inner != 0) {
        inner->value = value;
    }
}