struct A;
typedef long long (*Fn)(A*);

struct A {
    Fn* vtable;
};

struct B {
    char pad[0x3c];
    A* a;
};

extern "C" long long func_6130fb48(B* b) {
    A* a = b->a;
    if (!a)
        return 0;
    return a->vtable[3](a);
}