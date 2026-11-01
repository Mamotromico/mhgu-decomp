struct Func6001d9f8Args {
    unsigned char padding0[0x230];
    unsigned char field_230;
    unsigned char padding1[0xbf];
    unsigned char field_2f0;
};

extern "C" int func_6001d9f8(Func6001d9f8Args* self) {
    if (self->field_230) {
        return 1;
    }
    return self->field_2f0 != 0;
}