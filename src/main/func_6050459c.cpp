struct S {
    char pad[0x350];
    int field;
};

extern "C" int func_6050459c(struct S *s)
{
    return s->field == 2 ? 1 : 0;
}