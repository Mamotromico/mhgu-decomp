struct inner_60071434 {
    unsigned char pad[0xc2];
    unsigned char value;
};

struct outer_60071434 {
    unsigned char pad[0x75e8];
    inner_60071434 *ptr;
};

extern "C" unsigned char func_60071434(outer_60071434 *arg)
{
    return arg->ptr->value;
}