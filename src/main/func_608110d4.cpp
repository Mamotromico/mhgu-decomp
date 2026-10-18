struct VTable {
    char pad[0x20];
    void (*f)(void *);
};

struct Obj {
    VTable *vt;
};

extern "C" void func_608110d4(struct Obj *obj) {
    obj->vt->f(obj);
}