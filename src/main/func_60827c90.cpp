struct func_60827c90_t {
    unsigned char pad[0x18];
    void (*fn)(void *, void *);
};

struct func_60827c90_s {
    struct func_60827c90_t *t;
};

extern "C" void func_60827c90(struct func_60827c90_s *s, void *x)
{
    s->t->fn(s, x);
}