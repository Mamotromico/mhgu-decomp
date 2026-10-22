struct S {
    unsigned char pad[0x30];
    unsigned int field;
};

extern "C" void func_6092289c(S *p, unsigned int v) {
    if ((p->field & 0x3f00u) == 0)
        v &= 0xf7u;
    *(unsigned char *)&p->field = v;
}