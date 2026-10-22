typedef void (*InnerFn)(void *, unsigned short);

struct Inner {
    unsigned char pad[0xc0];
    InnerFn fn;
};

struct Outer {
    Inner *inner;
    unsigned char pad[0x4b0];
    unsigned short value;
};

extern "C" void func_6053a058(Outer *self) {
    self->inner->fn(self, self->value);
}