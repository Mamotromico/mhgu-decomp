struct Inner {
    char pad0[0x18];
    void *(*fn)(void *, void *);
};

struct A {
    char pad0[4];
    void *field4;
};

struct B {
    struct Inner *inner;
};

extern "C" void *func_604ba7fc(struct A *a, struct B *b) {
    return b->inner->fn((void *)b, a->field4);
}