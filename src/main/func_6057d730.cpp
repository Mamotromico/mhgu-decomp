struct A;

struct VTable {
    char pad[0x24];
    void (*fn)(A*);
};

struct A {
    VTable* vtable;
};

struct Container {
    char pad[0x4c];
    A* a;
};

extern "C" void func_6057d730(Container* c) {
    A* a = c->a;
    a->vtable->fn(a);
}