struct Target;

struct VTable {
    void *slots[5];
    void (*method)(Target *);
};

struct Target {
    VTable *vptr;
};

struct Container {
    char pad[0x10];
    Target *target;
};

extern "C" void func_613c29c4(Container *c) {
    Target *t = c->target;
    if (t) {
        t->vptr->method(t);
    }
}