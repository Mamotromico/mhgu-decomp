struct Inner {
    unsigned char pad[0x527];
    unsigned char field_527;
};

struct Outer {
    unsigned char pad[0x1428];
    struct Inner *inner;
};

extern "C" void func_600c2660(struct Outer *arg)
{
    struct Inner *p = arg->inner;
    if (p->field_527 & 1)
        p->field_527 &= 0xFE;
}