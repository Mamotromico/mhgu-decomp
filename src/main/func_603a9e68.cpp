struct Inner {
    char pad0[0x3c];
    unsigned int field_0x3c;
};

struct Top {
    char pad0[0xa4];
    Inner *field_0xa4;
};

extern "C" unsigned int func_603a9e68(Top *p) {
    return p->field_0xa4 ? p->field_0xa4->field_0x3c : 0;
}