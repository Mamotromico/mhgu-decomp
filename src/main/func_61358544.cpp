struct S {
    unsigned char pad[0x254];
    unsigned int value;
};

extern "C" unsigned int func_61358544(S *s) {
    unsigned int v = s->value;
    return v == 1 ? v : 0;
}