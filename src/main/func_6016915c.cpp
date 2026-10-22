struct func_6016915c_target {
    unsigned char pad0[0x30];
    unsigned int field30;
    unsigned char pad1[0x90 - 0x34];
    unsigned short field90;
    unsigned short field92;
};

extern "C" void func_6016915c(func_6016915c_target *p, unsigned short a, unsigned short b) {
    p->field30 |= 0x20000u;
    p->field90 = a;
    p->field92 = b;
}