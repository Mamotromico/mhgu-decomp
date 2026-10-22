struct Inner_60068dc4 {
    char pad0[0x64];
    int value;
};

struct Outer_60068dc4 {
    char pad0[0x257c];
    Inner_60068dc4 *inner;
};

extern "C" int func_60068dc4(Outer_60068dc4 *outer) {
    Inner_60068dc4 *p = outer->inner;
    return p ? p->value : 0;
}