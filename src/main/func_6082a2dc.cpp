struct Object;

struct VTable {
    char pad[0x50];
    void (*fn)(Object *, void *);
};

struct Object {
    VTable *vtable;
    int pad;
    void *field8;
};

extern "C" void func_6082a2dc(Object *obj) {
    obj->vtable->fn(obj, obj->field8);
}