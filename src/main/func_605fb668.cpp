struct S_605fb668 {
    unsigned char pad_0[0x58];
    unsigned char field_58;
    unsigned char pad_59[0x08];
    unsigned char field_61;
};

extern "C" void func_605fb668(S_605fb668 *s, unsigned char value)
{
    s->field_58 |= 0x20;
    s->field_61 = value;
}