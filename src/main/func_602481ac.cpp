struct func_602481ac_state {
    char pad0[0x5b1];
    unsigned char field_5b1;
    char pad1[0xa];
    unsigned char field_5bc;
};

extern "C" void func_602481ac(func_602481ac_state *s) {
    unsigned char v = s->field_5bc;
    if (v & 0x2) return;
    if (s->field_5b1 & 0x8) s->field_5bc = v | 0x2;
}