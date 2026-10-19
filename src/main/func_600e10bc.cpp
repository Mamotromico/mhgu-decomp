struct S {
    unsigned char pad[4];
    unsigned char field_4;
};

extern "C" int func_600e10bc(const S *s, unsigned int mask)
{
    return (s->field_4 & mask) != 0;
}