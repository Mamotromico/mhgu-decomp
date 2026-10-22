struct Inner {
    unsigned char pad[0x522];
    unsigned char flag;
};

struct Outer {
    unsigned char pad[0x1428];
    struct Inner *p;
};

extern "C" int func_60081dbc(struct Outer *s) {
    return s->p->flag != 0;
}