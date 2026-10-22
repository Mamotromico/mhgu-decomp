struct Outer;

typedef void (*InnerFn)(struct Outer *, int, int);

struct Inner {
    unsigned char pad0[0x40];
    InnerFn fn;
};

struct Outer {
    struct Inner *inner;
    unsigned char pad0[0x14];
    int value;
};

extern "C" void func_613c2f50(struct Outer *self, int a, int b, int c)
{
    self->value = a;
    self->inner->fn(self, b, c);
}