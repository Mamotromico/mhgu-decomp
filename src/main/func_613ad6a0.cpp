struct VTable {
    char pad0[0x2c];
    void (*method)(void *, void *);
};

struct Obj {
    VTable *vtbl;
};

struct Mid {
    char pad0[0x40];
    Obj *obj;
};

struct Top {
    char pad0[0x10];
    Mid *mid;
};

extern "C" void func_613ad6a0(Top *t, void *ctx) {
    Obj *o = t->mid->obj;
    o->vtbl->method(o, ctx);
}