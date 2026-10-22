struct Inner {
    char pad[8];
    int value;
};

struct Outer {
    char pad[0x208];
    struct Inner *inner;
};

extern "C" int func_60ba84f0(struct Outer *outer) {
    struct Inner *inner = outer->inner;
    return inner ? inner->value : 0;
}