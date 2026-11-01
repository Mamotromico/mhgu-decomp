struct VTable {
    char pad[0x44];
    int (*fn)(void *);
};

struct Object {
    struct VTable *vtable;
};

struct Container {
    char pad[0x54];
    struct Object *obj;
};

extern "C" int func_60966864(struct Container *c) {
    struct Object *o = c->obj;
    if (!o) return 0;
    return o->vtable->fn(o);
}