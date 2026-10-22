struct S0 {
    int field_0;
};

struct S1 {
    char pad_0[4];
    unsigned char field_4;
};

extern "C" void func_613ef6c4(S0 *a, S1 *b) {
    b->field_4 = 1;
    a->field_0 = 0;
}