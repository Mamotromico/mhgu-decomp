struct VTable {
    void *pad[15];
    void (*fn)(void *, unsigned char);
};

struct Inner {
    VTable *vtable;
};

struct Outer {
    char pad0[0x4d];
    unsigned char b;
    char pad1[0x0e];
    Inner *p;
};

extern "C" void func_60642564(Outer *self) {
    Inner *obj = self->p;
    VTable *vt = obj->vtable;
    void (*fn)(void *, unsigned char) = vt->fn;
    unsigned char arg = self->b;
    fn(obj, arg);
}