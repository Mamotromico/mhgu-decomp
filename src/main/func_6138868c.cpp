struct S {
    char pad0[0x74];
    unsigned int field_74;
    char pad1[0x02];
    unsigned char field_7a;
};

extern "C" void func_6138868c(S *s, unsigned int value) {
    if (s->field_74 == value) {
        s->field_7a = 1;
    }
}