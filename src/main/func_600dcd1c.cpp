struct S_600dcd1c {
    unsigned char pad_0[4];
    unsigned short field_4;
    unsigned char pad_6[0x16];
    unsigned char field_1c;
};

extern "C" int func_600dcd1c(S_600dcd1c *self) {
    int result = 0;
    if ((self->field_4 & 0x1f) == 0x14)
        result = self->field_1c;
    return result;
}