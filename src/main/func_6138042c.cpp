struct B;

struct VTable {
    char pad[0x10];
    void *(*fn)(B *);
};

struct B {
    VTable *vtable;
};

struct A {
    char pad[0xa4];
    B *b;
};

extern "C" void *func_6138042c(A *a) {
    B *b = a->b;
    if (!b)
        return 0;
    return b->vtable->fn(b);
}