struct A {
    int pad0;
    void* field4;
};

struct B {
    void** vtable;
};

typedef int (*Fn)(B*, void*);

extern "C" int func_601121b4(A* a, B* b) {
    return ((Fn)b->vtable[3])(b, a->field4);
}