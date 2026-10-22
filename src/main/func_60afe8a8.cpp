struct A {
    void *field0;
    unsigned int field4;
    void *field8;
};

struct B {
    char pad[0x10];
    void *field10;
};

extern "C" void func_60afe8a8(A *a, B *b) {
    a->field4 = 0;
    a->field8 = b->field10;
    a->field0 = b;
}