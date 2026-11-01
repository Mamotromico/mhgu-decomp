struct func_600dccec_layout {
    unsigned char pad0[4];
    unsigned short field_4;
    unsigned char pad6[0x12 - 6];
    unsigned char field_12;
};

extern "C" unsigned char func_600dccec(const func_600dccec_layout *p) {
    unsigned char result = 0;
    if ((p->field_4 & 0x1f) == 0x14)
        result = p->field_12;
    return result;
}