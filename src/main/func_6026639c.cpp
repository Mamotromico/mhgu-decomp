struct S {
    unsigned char pad[0x2748];
    unsigned char field;
};

extern "C" unsigned char func_6026639c(S* p) {
    return p->field ^ 1;
}