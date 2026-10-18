struct B {
    char _pad[16];
    void *value;
};

struct A {
    struct B *b;
};

extern "C" void *func_60bf8320(struct A *a)
{
    return a->b->value;
}