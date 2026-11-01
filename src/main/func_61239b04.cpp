extern "C" int func_61239b04(char *p, unsigned v)
{
    struct inner {
        char pad0[0x10];
        unsigned f10;
        unsigned f14;
        unsigned f18;
    };
    struct outer {
        char pad0[0x8];
        struct inner *p8;
    };
    struct outer *o = (struct outer *)p;
    struct inner *q = o->p8;
    unsigned a = q->f14;
    unsigned b = q->f18;
    unsigned d = a - b;
    int r = 0;
    if (d >= v) {
        r = 1;
        q->f10 = v;
    }
    return r;
}