struct S {
    unsigned char pad0[4];
    unsigned short field4;
    unsigned char pad6[0x14 - 0x6];
    unsigned char field14;
};

extern "C" int func_600dce2c(const S *s) {
    return ((s->field4 & 0x1f) == 0x14) ? s->field14 : 0;
}