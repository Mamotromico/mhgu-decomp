struct Inner;

struct VTable {
    char pad[0x3c];
    int (*fn)(Inner *);
};

struct Inner {
    VTable *vtable;
};

struct Outer {
    int pad;
    Inner *inner;
};

extern "C" int func_6083824c(Outer *o) {
    Inner *p = o->inner;
    if (!p) return 0;
    return p->vtable->fn(p);
}