struct VTable;

struct Sub {
    VTable *vptr;
};

struct VTable {
    char pad[0x24];
    void (*fn)(Sub*);
};

struct Obj {
    char pad[0x708];
    Sub sub;
};

extern "C" void func_613c07f8(Obj *obj) {
    obj->sub.vptr->fn(&obj->sub);
}