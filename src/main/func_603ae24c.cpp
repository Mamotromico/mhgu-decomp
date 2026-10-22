struct S603ae24c {
    unsigned char pad[0x50];
    unsigned char field;
};

extern "C" int func_603ae24c(S603ae24c *s, int value)
{
    return s->field == value;
}