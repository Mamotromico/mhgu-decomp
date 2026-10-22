struct inner_600c267c {
    unsigned char pad_0[0x527];
    unsigned char field_527;
};

struct outer_600c267c {
    unsigned char pad_0[0x1428];
    inner_600c267c *field_1428;
};

extern "C" void func_600c267c(outer_600c267c *arg0, unsigned int arg1)
{
    inner_600c267c *p = arg0->field_1428;
    unsigned char value = p->field_527;

    if (value & arg1) {
        p->field_527 = value & ~arg1;
    }
}