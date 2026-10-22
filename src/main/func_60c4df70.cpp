struct S {
    unsigned char pad0[4];
    unsigned char field4;
    unsigned char field5;
    unsigned char pad1[2];
    int field8;
};

extern "C" void func_60c4df70(S *s, int a, int b)
{
    s->field4 = a;
    if (a != 0) {
        s->field5 = 1;
        s->field8 = b;
    }
}