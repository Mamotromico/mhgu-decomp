struct Inner;

struct Vtable {
    void *unused[0x13];
    int (*method)(Inner *, int);
};

struct Inner {
    Vtable *vtable;
};

struct Outer {
    char pad[0x60];
    Inner *inner;
};

extern "C" int func_60ba1e34(Outer *obj, int arg) {
    Inner *inner = obj->inner;
    if (!inner)
        return 0;
    return inner->vtable->method(inner, arg);
}