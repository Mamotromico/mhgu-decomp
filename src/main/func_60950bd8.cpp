struct S {
    unsigned char pad[6];
    unsigned char field;
};

extern "C" int func_60950bd8(const S *s)
{
    return (s->field & 5) != 0;
}