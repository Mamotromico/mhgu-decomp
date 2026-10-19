struct S_613a79a8 {
    unsigned char pad_00[0x2c];
    unsigned int field_2c;
    unsigned char pad_30[0x04];
    unsigned int field_34;
};

extern "C" void func_613a79a8(S_613a79a8 *s, unsigned int value)
{
    if (s->field_2c >= value) {
        s->field_34 = value;
    }
}