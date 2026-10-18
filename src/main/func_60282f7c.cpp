extern "C" void func_60282f7c(struct S *self);

struct S {
    void **vtable;
};

extern "C" void func_60282f7c(struct S *self)
{
    ((void (*)(struct S *))self->vtable[189])(self);
}