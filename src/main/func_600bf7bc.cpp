struct Inner_600bf7bc {
    char pad_0[0x5c];
    float field_5c;
    char pad_60[0x1b9 - 0x60];
    unsigned char field_1b9;
};

struct Outer_600bf7bc {
    char pad_0[0x1428];
    Inner_600bf7bc * volatile field_1428;
};

extern "C" void func_600bf7bc(Outer_600bf7bc *p, float value) {
    p->field_1428->field_5c = value;
    p->field_1428->field_1b9 = 1;
}