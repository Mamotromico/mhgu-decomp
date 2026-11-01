extern "C" int func_60544fe8(const unsigned char *obj, unsigned int idx)
{
    struct Layout {
        unsigned char pad0[0xf8];
        int *array;
        unsigned char pad1[0x294 - 0xf8 - 4];
        unsigned int base;
        unsigned int count;
    };
    const Layout *o = (const Layout *)obj;
    if (o->count > idx)
        return o->array ? o->array[idx] : 0;
    return ((int *)o->base)[idx - o->count];
}