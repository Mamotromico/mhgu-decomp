struct Inner_613101e0 {
    char pad_0[0x10];
    unsigned int value;
};

struct Outer_613101e0 {
    char pad_0[0x5c];
    struct Inner_613101e0 *inner;
};

extern "C" unsigned int func_613101e0(struct Outer_613101e0 *outer) {
    struct Inner_613101e0 *inner = outer->inner;
    return inner ? inner->value : 0;
}