struct Inner {
    unsigned char pad_0[0x78];
    void *field_78;
    unsigned char pad_7c[0xc4 - 0x7c];
    unsigned char field_c4;
};

struct Outer {
    unsigned char pad_0[0x75e8];
    Inner *field_75e8;
};

extern "C" void *func_60071388(Outer *obj) {
    Inner *inner = obj->field_75e8;
    return inner->field_c4 != 0 ? inner->field_78 : 0;
}