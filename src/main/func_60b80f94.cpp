struct Inner {
    char pad0[0x28];
    unsigned int count;      // +0x28
    char pad1[0xa4 - 0x28 - 4];
    char *list;              // +0xa4
};

struct Outer {
    char pad0[0x64];
    Inner *inner;            // +0x64
};

struct Entry {
    unsigned int key;        // +0x0
    char pad0[0x18 - 4];
};

extern "C" Entry *func_60b80f94(Outer *o, unsigned int key)
{
    Inner *in = o->inner;
    unsigned int n = in->count;
    if (n == 0)
        return 0;
    Entry *e = (Entry *)in->list;
    for (unsigned int i = 0; i < n; i++, e++) {
        if (e->key == key)
            return e;
    }
    return 0;
}