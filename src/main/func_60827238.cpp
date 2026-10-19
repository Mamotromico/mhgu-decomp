struct Object;

struct VTable {
    unsigned char pad0[0x30];
    void (*method30)(Object *);
};

struct Object {
    VTable *vtable;
};

struct Outer {
    unsigned char pad0[4];
    Object *object;
};

extern "C" void func_60827238(Outer *arg) {
    Object *obj = arg->object;
    obj->vtable->method30(obj);
}