struct S_603193a4 {
    char pad0[0x38];
    int field38;
    char pad3C[0x52 - 0x3C];
    unsigned short field52;
    unsigned char field54;
};

extern "C" void func_603193a4(S_603193a4 *s, unsigned short value52, unsigned char value54) {
    s->field38 = 0;
    s->field52 = value52;
    s->field54 = value54;
}