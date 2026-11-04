extern "C" int func_60b810e4(void *self, int key);

struct Inner {
    char pad0[0x4];
    int field4;
};

struct Outer {
    char pad0[0x74];
    int count;          // +0x74
    char pad78[0xec - 0x78];
    Inner *list;        // +0xec
};

extern "C" int func_60b810e4(void *p, int key)
{
    Outer *o = *(Outer **)((char *)p + 0x64);
    Inner *e;
    unsigned int i;
    unsigned int n;

    if (o->list == 0)
        return 0;
    n = (unsigned int)o->count;
    if (n == 0)
        return 0;

    e = o->list;
    i = 0;
    do {
        if (e->field4 == key)
            return (int)e;
        i++;
        e = (Inner *)((char *)e + 0xc);
    } while (i < n);
    return 0;
}