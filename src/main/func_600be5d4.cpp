struct Inner {
    char pad0[0x1ac];
    float a;
    float b;
};

struct Outer {
    char pad0[0x1428];
    Inner* inner;
};

extern "C" float func_600be5d4(Outer* outer) {
    return outer->inner->a * outer->inner->b;
}