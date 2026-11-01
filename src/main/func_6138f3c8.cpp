struct Object;

struct VTable {
    void *entries[10];
    void *(*fn)(Object *);
};

struct Object {
    VTable *vtable;
};

struct Outer {
    char pad[8];
    Object *obj;
};

extern "C" void *func_6138f3c8(Outer *self) {
    Object *obj = self->obj;
    if (obj == 0)
        return 0;
    return obj->vtable->fn(obj);
}