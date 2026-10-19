struct S_612d0978 {
    char pad0[0x84];
    unsigned char field84;
    char pad1[0x8c - 0x85];
    unsigned short field8c;
    char pad2[0x01];
};

extern "C" void func_612d0978(S_612d0978* p, unsigned char v) {
    p->field84 = v;
    p->field8c = 1;
}