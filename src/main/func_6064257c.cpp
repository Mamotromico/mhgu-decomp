extern "C" unsigned func_6064257c(char *self)
{
    void *obj = *(void **)(self + 0x5c);
    unsigned (*fn)(void *) = *(unsigned (**)(void *))((char *)*(void **)obj + 0x38);
    unsigned idx = fn(obj);
    unsigned *arr = *(unsigned **)(self + 0x54);
    return arr[idx];
}