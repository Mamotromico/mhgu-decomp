struct Inner;
struct VTable {
    char pad[0x8c];
    int (*method)(struct Inner *);
};
struct Inner {
    struct VTable *vtable;
};
struct Outer {
    char pad[0x60];
    struct Inner *inner;
};

extern "C" int func_605d3fa4(struct Outer *o) {
    struct Inner *inner = o->inner;
    if (!inner) return 0;
    return inner->vtable->method(inner);
}