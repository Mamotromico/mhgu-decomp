struct Obj;
typedef void* (*Method)(Obj*);

struct Vtbl {
    char pad[0x44];
    Method method;
};

struct Obj {
    Vtbl* vtbl;
};

struct Container {
    char pad[0x4];
    Obj* obj;
};

extern "C" void* func_6083805c(Container* c) {
    Obj* o = c->obj;
    if (!o) return 0;
    return o->vtbl->method(o);
}