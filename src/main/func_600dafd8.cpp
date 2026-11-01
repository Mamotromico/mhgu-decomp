struct S {
    unsigned char pad0[4];
    unsigned short type;
    unsigned char pad1[0x0a];
    unsigned int value;
};

extern "C" unsigned int func_600dafd8(const S *s) {
    unsigned int t = s->type & 0x1f;
    if (t == 0x0d || t == 0x0b)
        return s->value;
    return 0;
}