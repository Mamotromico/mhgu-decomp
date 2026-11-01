struct S {
    char pad0[0x18];
    void (*cb)(S *, void *);
    char pad1[4];
    char field20;
    char pad2[0xF];
    int field30;
};

extern "C" void func_61237010(S *s) {
    s->field30 = 5;
    void (*cb)(S *, void *) = s->cb;
    if (cb) {
        cb(s, &s->field20);
    }
}