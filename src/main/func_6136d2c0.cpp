struct Inner;
struct Vtable {
    char pad[0x60];
    void (*method)(struct Inner*, void*, void*);
};
struct Inner {
    struct Vtable* vtable;
};
struct Outer {
    void* unknown;
    struct Inner* inner;
    void* arg;
};
extern "C" void func_6136d2c0(struct Outer* o, void* arg) {
    struct Inner* i = o->inner;
    i->vtable->method(i, o->arg, arg);
}