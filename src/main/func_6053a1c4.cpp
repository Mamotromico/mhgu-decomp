typedef int (*fn_t)(void *, int, int, int);

struct Inner {
    char pad[0xc4];
    fn_t fn;
};

struct Outer {
    struct Inner *inner;
};

extern "C" int func_6053a1c4(struct Outer *self, int a, int b)
{
    return self->inner->fn(self, 1, a, b);
}