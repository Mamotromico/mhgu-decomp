struct S {
    unsigned char pad[4];
    unsigned char field;
};

extern "C" int func_600e10f0(const S *s)
{
    return (s->field & 3) == 3;
}