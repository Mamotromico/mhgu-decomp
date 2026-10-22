struct Inner_600c03a0 {
    char pad_0000[0x5dec];
    int  field_5dec;
};

struct Outer_600c03a0 {
    char pad_0000[0x1428];
    Inner_600c03a0 *ptr_1428;
};

extern "C" void func_600c03a0(Outer_600c03a0 *p)
{
    p->ptr_1428->field_5dec = 2;
}