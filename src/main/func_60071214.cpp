extern "C" int func_60071214(void *self, unsigned idx);

struct Vtbl {
    char pad0[0x1b8];
    int (*fn)(void *self, unsigned idx);
};

struct Root {
    Vtbl *vptr;
};

struct Inner {
    char pad0[0x68];
    struct {
        char pad0[0x8];
        unsigned char b;
    } *arr;
};

extern "C" int func_60071214(void *self, unsigned idx)
{
    if (idx >= 8) {
        struct Root *r = (struct Root *)self;
        return r->vptr->fn(self, idx);
    }
    unsigned char *base = (unsigned char *)self;
    Inner *p = *(Inner **)(base + 0x75ec);
    unsigned char *e = (unsigned char *)p->arr + idx * 5 * 2;
    return *(unsigned char *)(e + 0x8);
}