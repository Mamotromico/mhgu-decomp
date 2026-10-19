struct S_6026e7b8 {
    unsigned char pad_0[0x504];
    unsigned short field_504;
};

extern "C" int func_6026e7b8(const S_6026e7b8 *p) {
    return p->field_504 & 3;
}