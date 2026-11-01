struct str_600dcebc {
    char pad0[4];
    unsigned short field_4;
    char pad6[0x15];
    unsigned char field_1b;
};

extern "C" unsigned char func_600dcebc(const struct str_600dcebc *p) {
    if ((p->field_4 & 0x1f) == 0x14)
        return p->field_1b;
    return 0;
}