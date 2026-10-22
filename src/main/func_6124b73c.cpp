struct Outer;
struct Inner;

struct Vtable {
    char pad[0x2c];
    void (*fn)(Inner*, Outer*);
};

struct Inner {
    Vtable* vtable;
};

struct Outer {
    char pad[4];
    Inner* inner;
};

extern "C" void func_6124b73c(Outer* self) {
    Inner* inner = self->inner;
    inner->vtable->fn(inner, self);
}