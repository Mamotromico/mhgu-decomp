struct A {
    void *field0;
};

struct B {
    char pad[4];
    void *field4;
};

struct C {
    char pad[0xc];
    void (*fieldc)(A *, void *);
};

extern "C" void func_600fa7b4(B *a, A *b) {
    C *c = (C *)b->field0;
    c->fieldc(b, a->field4);
}