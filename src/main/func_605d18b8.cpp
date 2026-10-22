struct Inner;
struct VTable {
    char pad[0x94];
    int (*fn)(Inner *, int, int);
};
struct Inner {
    VTable *vtable;
};
struct Outer {
    char pad[0x4c];
    Inner *inner;
};

extern "C" int func_605d18b8(Outer *o, int arg) {
    Inner *inner = o->inner;
    VTable *vt = inner->vtable;
    return vt->fn(inner, arg, 0);
}