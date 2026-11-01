extern "C" int func_60c71898(void *self, unsigned index);

struct Inner {
    char pad[0x50];
    unsigned char field_50;
};

struct Outer {
    char pad0[0x3c];
    unsigned count;
    char pad1[0x48 - 0x3c - 4];
    Inner **items;
};

extern "C" int func_60c71898(void *self, unsigned index)
{
    Outer *p = (Outer *)self;
    if (p->count <= index)
        return 0;
    Inner *e = p->items[index];
    if (e->field_50)
        return 1;
    return 0;
}