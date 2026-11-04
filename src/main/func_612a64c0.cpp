struct Inner {
    char pad0[0xC];
    int field_c;
    int field_10;
    char pad14[0x4];
    int field_18;
};

struct S {
    char pad0[0x4];
    unsigned char field_4;
    char pad5[0x3];
    Inner *field_8;
    int field_c;
};

extern "C" int func_612a64c0(S *s) {
    Inner *in = s->field_8;
    int r3 = in->field_10 - s->field_c;
    if ((unsigned)r3 <= 3) {
        s->field_4 = 1;
        return 0;
    }
    unsigned char *base = (unsigned char *)in->field_c;
    base += in->field_18;
    int off = s->field_c;
    unsigned char *p = base + off;
    unsigned int b0 = p[0];
    off += 4;
    unsigned int b1 = p[1];
    unsigned int b2 = p[2];
    unsigned int b3 = p[3];
    s->field_c = off;
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24);
}