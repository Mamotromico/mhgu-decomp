struct Obj;

struct VTable {
    char pad0[0x50];
    void (*fn50)(Obj *);
};

struct Obj {
    VTable *vt;
    char pad1[0xb8];
    unsigned int field_bc;
};

extern "C" void func_60a530bc(Obj *self, unsigned int *p) {
    unsigned int v = *p;
    if (v == self->field_bc)
        return;
    self->field_bc = v;
    self->vt->fn50(self);
}