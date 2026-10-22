struct B;
struct C {
    char pad[0xc];
    void (*fn)(B*, void*);
};
struct B {
    C* c;
};
struct A {
    char pad[4];
    void* field4;
};
extern "C" void func_60117b6c(A* a, B* b) {
    b->c->fn(b, a->field4);
}