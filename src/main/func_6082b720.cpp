struct S {
    int pad0[2];
    int field8;
    char pad[0x424 - 12];
    unsigned char flag;
};

extern "C" void func_6082b720(S* s)
{
    if (s->field8 != 0x12)
        return;
    if (s->flag != 0)
        s->flag = 0;
}