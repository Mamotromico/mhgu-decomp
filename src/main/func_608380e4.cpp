struct A {
    void *vtable;
};

struct B {
    int dummy;
    A *a;
};

extern "C" int func_608380e4(B *b) {
    A *p = b->a;
    if (!p) return 0;
    int (*fn)(A*) = *(int (**)(A*))((char*)p->vtable + 0x48);
    return fn(p);
}