extern "C" {
struct Inner518 {
    unsigned char pad[0x518];
    unsigned char value;
};

struct Outer1428 {
    unsigned char pad[0x1428];
    Inner518 *inner;
};

int func_60081774(Outer1428 *outer) {
    Inner518 *inner = outer->inner;
    return inner->value == 2 ? 1 : 0;
}
}