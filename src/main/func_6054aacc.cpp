struct S_6054aacc {
    unsigned char pad[0x80];
    unsigned int value;
};

extern "C" int func_6054aacc(S_6054aacc *s)
{
    return (s->value - 3) > 1;
}