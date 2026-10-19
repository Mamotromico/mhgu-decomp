struct S {
    unsigned char pad[0x370];
    int (*cb)(void *, int);
};

extern "C" int func_6103a984(void *ctx) {
    struct S *s = *(struct S **)ctx;
    return s->cb(ctx, 1);
}