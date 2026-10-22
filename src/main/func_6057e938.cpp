struct inner_6057e938 {
    unsigned char pad[0x7c];
    int field;
};

struct outer_6057e938 {
    unsigned char pad0[0x4c];
    int field;
    unsigned char pad1[0x54];
    struct inner_6057e938 *ptr;
};

extern "C" void func_6057e938(struct outer_6057e938 *a, int b) {
    a->field = b;
    struct inner_6057e938 *p = a->ptr;
    if (p) {
        p->field = b;
    }
}