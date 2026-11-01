struct Inner;

typedef void* (*InnerMethod)(Inner*);

struct VTable {
    char pad[0x18];
    InnerMethod method;
};

struct Inner {
    VTable* vptr;
};

struct Outer {
    char pad[0x3c];
    Inner* inner;
};

extern "C" void* func_6138f544(Outer* o) {
    Inner* p = o->inner;
    if (p == 0)
        return 0;
    return p->vptr->method(p);
}