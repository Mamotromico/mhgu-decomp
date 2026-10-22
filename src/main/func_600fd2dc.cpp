struct VTable {
    char pad0[0xc];
    void (*call)(void *, void *);
};

struct B {
    VTable *vt;
};

struct A {
    char pad0[4];
    void *value;
};

extern "C" void func_600fd2dc(A *a, B *b)
{
    b->vt->call(b, a->value);
}