struct Outer;

typedef void (*InnerFn)(Outer *, int, int);

struct Inner {
    char pad[0x40];
    InnerFn fn;
};

struct Outer {
    Inner *inner;
};

extern "C" void func_613c2f94(Outer *o, int a, int b) {
    o->inner->fn(o, a, b);
}