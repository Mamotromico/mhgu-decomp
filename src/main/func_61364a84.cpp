struct Inner {
    char pad0;
    unsigned char field_1;
    unsigned short field_2;
};

struct Outer {
    int pad0;
    struct Inner *field_4;
    char pad8[2];
    unsigned char field_a;
    char pad_b[3];
    unsigned short field_e;
};

extern "C" int func_61364a84(struct Outer *o)
{
    struct Inner *p = o->field_4;
    o->field_a = p->field_1;
    o->field_e = p->field_2;
    return 1;
}