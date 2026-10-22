struct Object;

struct VTable {
    unsigned char pad[0xc];
    void (*call)(Object *, unsigned int);
};

struct Object {
    VTable *vtable;
};

struct Argument {
    unsigned char pad[4];
    unsigned int value;
};

extern "C" void func_600ffe04(Argument *arg, Object *obj) {
    obj->vtable->call(obj, arg->value);
}