struct S {
    unsigned char pad0[0xfec];
    volatile unsigned int x;
    unsigned char pad1[0x8a0];
    volatile unsigned int y;
    unsigned char pad2[0xc];
    volatile unsigned int z;
};

extern "C" void func_606cca14(S *s) {
    s->z = 0;
    s->y = s->x;
}