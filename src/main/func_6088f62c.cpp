struct FuncTable {
    char pad[0x60];
    int (*fn)(void *);
};

struct Obj {
    FuncTable *vt;
};

extern "C" int func_6088f62c(Obj *self) {
    return self->vt->fn(self);
}