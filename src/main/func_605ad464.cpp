extern "C" unsigned char func_605ad464(char *p)
{
    void *obj = *(void **)(p + 0x4c);
    unsigned (*fn)(void *) = *(unsigned (**)(void *))(*(char **)obj + 0x38);
    unsigned idx = fn(obj);
    char *base = *(char **)(p + 0x5c);
    return (unsigned char)base[idx];
}