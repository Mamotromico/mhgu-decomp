struct S606efee8 {
    unsigned char pad0[0x70];
    unsigned char *ptr;
    unsigned char pad74[2];
    unsigned char byte76;
};

extern "C" int func_606efee8(S606efee8 *s, int idx)
{
    return s->ptr[(unsigned char)idx] == s->byte76;
}