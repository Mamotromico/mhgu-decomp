struct Impl {
    unsigned char pad0[0x3dc];
    void (*method)(void *);
};

struct Object {
    Impl *impl;
};

extern "C" void func_600ca10c(Object *self)
{
    self->impl->method(self);
}