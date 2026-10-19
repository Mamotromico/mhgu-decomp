struct VTable {
    char pad[0x24];
    void (*fn)(void *);
};

struct Sub {
    VTable *vptr;
};

struct Outer {
    char pad[0xb58];
    Sub sub;
};

extern "C" void func_613c07ec(Outer *o) {
    o->sub.vptr->fn(&o->sub);
}