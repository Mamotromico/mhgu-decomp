struct s600e83a8 {
    unsigned char pad[0x2f8];
    unsigned short field;
};

extern "C" unsigned short *func_600e83a8(struct s600e83a8 *p) {
    unsigned short *q = &p->field;
    *q = (unsigned short)(*q + 1);
    return q;
}