struct S {
    unsigned char pad[0x1c];
    unsigned int field;
};

extern "C" int func_603f8678(struct S *s) {
    unsigned int v = s->field;
    int ret = 0;
    if (v - 2u < 3u)
        ret = 1;
    return ret;
}