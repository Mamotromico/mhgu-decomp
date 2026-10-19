struct Inner;

struct VTable {
    unsigned char pad[0x44];
    void (*fn)(Inner *, int);
};

struct Inner {
    VTable *vtable;
};

struct Outer {
    unsigned char pad[0x75e4];
    Inner *inner;
};

extern "C" void func_6006f6e8(Outer *outer, int dummy) {
    Inner *inner = outer->inner;
    inner->vtable->fn(inner, dummy);
}