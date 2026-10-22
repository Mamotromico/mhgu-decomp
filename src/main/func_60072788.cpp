struct S {
    unsigned char pad[0x4b4];
    unsigned short field;
};

extern "C" int func_60072788(S* s, int v) {
    return s->field == v;
}