extern "C" {

struct S {
    char pad0[0x28e0];
    unsigned short field_28e0;
    char pad1[0x2];
    unsigned int field_28e4;
    unsigned char field_28e8;
    char pad2[0x3];
};

void func_602f5760(S* s) {
    s->field_28e0 = 0;
    s->field_28e4 = 0;
    s->field_28e8 = 0;
}

}