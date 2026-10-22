struct arg0_layout {
    char pad_0[4];
    void *value;
};

struct arg1_layout {
    void *inner;
};

struct inner_layout {
    char pad_0[0xc];
    void (*fn)(void *, void *);
};

extern "C" void func_6010f68c(struct arg0_layout *a, struct arg1_layout *b) {
    ((struct inner_layout *)b->inner)->fn(b, a->value);
}