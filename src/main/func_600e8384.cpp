struct S {
    unsigned char pad[0x2f8];
    unsigned short field;
};

extern "C" unsigned short func_600e8384(const struct S *p) {
    return p->field;
}