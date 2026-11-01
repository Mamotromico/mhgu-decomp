struct Inner;

struct VTable {
    unsigned char padding[0x14];
    void (*slot5)(Inner *, void *);
};

struct Inner {
    VTable *vtable;
};

struct Outer {
    unsigned char padding[0xa4];
    Inner *inner;
};

extern "C" void func_6137fb40(Outer *self, void *ctx) {
    Inner *p = self->inner;
    if (p == 0)
        return;
    p->vtable->slot5(p, ctx);
}