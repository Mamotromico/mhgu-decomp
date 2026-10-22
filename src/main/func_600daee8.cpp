struct S {
    char pad[4];
    unsigned short field;
};

extern "C" int func_600daee8(const S *s) {
    unsigned int v = s->field & 0x1fU;
    return (v - 7U) < 0x10U;
}