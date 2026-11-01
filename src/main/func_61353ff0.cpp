struct Object;

struct VTable {
    char pad[0x6c];
    int (*method_0x6c)(Object*);
};

struct Object {
    VTable* vtable;
};

struct Container {
    char pad[0x10];
    Object* field_0x10;
};

extern "C" int func_61353ff0(Container* c) {
    Object* o = c->field_0x10;
    if (o == 0)
        return 0;
    return o->vtable->method_0x6c(o);
}