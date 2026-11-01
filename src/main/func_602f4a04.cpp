struct S {
    char pad0[0xfec];
    unsigned int field_0xfec;
    char pad1[0x14a0 - 0xfec - 4];
    unsigned int field_0x14a0;
    char pad2[0x3218 - 0x14a0 - 4];
    unsigned short field_0x3218;
};

extern "C" void func_602f4a04(struct S *s, unsigned int v) {
    unsigned int sum = (unsigned short)(s->field_0x3218 + v);
    s->field_0xfec = sum;
    s->field_0x14a0 = sum;
}