struct inner_60068ddc {
    unsigned char pad0[0x68];
    void *field_68;
};

struct outer_60068ddc {
    unsigned char pad0[0x257c];
    struct inner_60068ddc *field_257c;
};

extern "C" void *func_60068ddc(struct outer_60068ddc *p)
{
    struct inner_60068ddc *q = p->field_257c;
    return q ? q->field_68 : 0;
}