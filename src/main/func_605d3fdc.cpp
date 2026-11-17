extern "C" int func_605d3fdc(char *base, unsigned int idx) {
    if (idx > 3)
        return 0;
    void *p = *(void **)(base + 0x68 + idx * 4);
    if (!p)
        return 0;
    void *vtable = *(void **)p;
    int (*fn)(void *) = *(int (**)(void *))((char *)vtable + 0x8c);
    return fn(p);
}