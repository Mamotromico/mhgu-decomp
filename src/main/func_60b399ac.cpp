struct VTable {
    char pad[0x4c];
    int (*method)(void *);
};

struct Obj {
    VTable *vptr;
};

struct Outer {
    char pad[0x3d0];
    Obj *obj;
};

extern "C" int func_60b399ac(Outer *outer) {
    Obj *obj = outer->obj;
    if (!obj)
        return 0;
    return obj->vptr->method(obj);
}