struct Inner {
    char pad[0x524];
    unsigned char flag;
};

struct Outer {
    char pad[0x1428];
    Inner *p;
};

extern "C" int func_60081fc8(Outer *o) {
    return o->p->flag != 0;
}