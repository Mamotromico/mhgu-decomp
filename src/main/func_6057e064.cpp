struct S {
    char pad_0[0x4c];
    S* volatile field_4c;
    volatile unsigned int field_50;
    char pad_54[0x5c - 0x54];
    volatile unsigned int field_5c;
    char pad_60[0x7c - 0x60];
    volatile unsigned int field_7c;
};

extern "C" void func_6057e064(S* p, unsigned int value)
{
    p->field_50 = value;
    S* q = p->field_4c;
    if (q != 0) {
        q->field_7c = value;
    }
    p->field_5c |= 4;
}