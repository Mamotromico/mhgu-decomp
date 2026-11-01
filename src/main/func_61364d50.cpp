extern "C" {
struct Inner {
    unsigned char pad0;
    unsigned char field_1;
    unsigned short field_2;
};

struct Outer {
    unsigned char pad0[4];
    struct Inner *field_4;
    unsigned char pad8[2];
    unsigned char field_a;
    unsigned char pad_b[3];
    unsigned short field_e;
};

int func_61364d50(struct Outer *o) {
    struct Inner *p = o->field_4;
    o->field_a = p->field_1;
    o->field_e = p->field_2;
    return 1;
}
}