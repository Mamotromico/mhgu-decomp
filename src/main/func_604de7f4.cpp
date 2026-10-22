struct Outer_604de7f4;

struct Inner_604de7f4
{
    unsigned char pad_0[0x18];
    void (*field_18)(volatile Outer_604de7f4 *);
};

struct Outer_604de7f4
{
    Inner_604de7f4 *field_0;
    unsigned char pad_4[0x1a91];
    unsigned char field_1a95;
};

extern "C" void func_604de7f4(volatile Outer_604de7f4 *self)
{
    self->field_1a95 = 0;
    self->field_0->field_18(self);
}