struct VTable {
    char pad[0xc];
    void (*fn)(void *, void *);
};

struct Arg1 {
    VTable *vtable;
};

struct Arg0 {
    char pad[4];
    void *arg;
};

extern "C" void func_6011e2bc(Arg0 *a, Arg1 *b)
{
    b->vtable->fn(b, a->arg);
}