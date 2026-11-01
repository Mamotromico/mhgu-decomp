struct Object;

struct Vtable {
    char pad[0x40];
    void *(*fn)(Object *);
};

struct Object {
    Vtable *vtable;
};

struct Container {
    char pad[0x75d0];
    Object *obj;
};

extern "C" void *func_600710d0(Container *c)
{
    Object *o = c->obj;
    if (o == 0)
        return 0;
    return o->vtable->fn(o);
}