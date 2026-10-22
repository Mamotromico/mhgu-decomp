struct inner {
    char pad[0xe];
    unsigned char value;
};

struct outer {
    char pad[0xa4];
    struct inner *ptr;
};

extern "C" int func_603a8cb4(struct outer *obj) {
    struct inner *p = obj->ptr;
    return (signed char)(p ? p->value : 0);
}