struct Sub_61082644 {
    char pad_0[0x3d0];
    void *(*fn_3d0)(void *, void *, void *);
};

struct Obj_61082644 {
    Sub_61082644 *p0;
};

extern "C" void *func_61082644(Obj_61082644 *self, void *a, void *b) {
    return self->p0->fn_3d0(self, a, b);
}