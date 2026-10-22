struct Inner_60602864 {
    unsigned char pad[0x94];
    void (*fn)(void *, int, int);
};

struct Outer_60602864 {
    Inner_60602864 *inner;
};

extern "C" void func_60602864(Outer_60602864 *self) {
    self->inner->fn(self, 1, 1);
}