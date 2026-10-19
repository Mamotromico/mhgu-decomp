extern "C" {
struct Inner_60071320 {
    char pad0[0x90];
    void *value;
};

struct Outer_60071320 {
    char pad0[0x75e8];
    Inner_60071320 *inner;
};

void *func_60071320(const Outer_60071320 *outer) {
    return outer->inner->value;
}
}