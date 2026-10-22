struct S {
    char pad[0x634];
    unsigned int field;
};

extern "C" int func_60677868(S *p)
{
    return ((p->field | 1u) == 9u) ? 1 : 0;
}