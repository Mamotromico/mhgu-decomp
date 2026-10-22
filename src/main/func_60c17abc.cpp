struct S_60c17abc {
    unsigned char pad_0[0x18];
    volatile int field_18;
    unsigned char pad_1c[0x8];
    volatile int field_24;
    volatile int field_28;
    volatile int field_2c;
};

extern "C" void func_60c17abc(struct S_60c17abc *s, int a, int b, int c, volatile int d)
{
    s->field_18 = a;
    int tmp = d;
    s->field_24 = b;
    s->field_28 = c;
    s->field_2c = tmp;
}