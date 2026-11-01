struct S {
    char pad0[4];
    volatile unsigned char field_4;
    volatile unsigned char field_5;
    char pad1[2];
    int field_8;
    int field_c;
    int field_10;
};

extern "C" void func_606a8220(S *self)
{
    self->field_4 = 0;
    self->field_5 = 0;
    self->field_8 = 7;
    self->field_c = 0;
    self->field_10 = 0;
}