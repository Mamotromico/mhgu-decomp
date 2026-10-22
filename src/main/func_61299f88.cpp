struct VT61299f88 {
    char pad0[0xc];
    void (*fn)(void *, unsigned int);
};

struct O61299f88 {
    VT61299f88 *vtbl;
};

struct A61299f88 {
    char pad0[0xc];
    unsigned int arg;
    O61299f88 *obj;
};

extern "C" void func_61299f88(A61299f88 *p) {
    unsigned int arg = p->arg;
    O61299f88 *obj = p->obj;
    obj->vtbl->fn(obj, arg);
}