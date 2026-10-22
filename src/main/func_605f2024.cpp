extern "C" {

struct S_605f2024 {
    unsigned char pad0[0x50];
    unsigned int  field_0x50;
    unsigned int  field_0x54;
};

void func_605f2024(S_605f2024 *self, unsigned int value)
{
    self->field_0x54 = value;
    self->field_0x50 |= 0x3u;
}

}