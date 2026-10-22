struct S_60282590 {
    char pad0[0x2549];
    unsigned char field_2549;
    char pad1[0x254c - 0x2549 - 1];
    int field_254c;
};

extern "C" void func_60282590(S_60282590 *s, int value) {
    s->field_2549 = 1;
    s->field_254c = value;
}