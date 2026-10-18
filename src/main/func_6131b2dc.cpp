struct func_6131b2dc_obj {
    unsigned char pad[0xcd8];
    unsigned char flags;
};

extern "C" unsigned int func_6131b2dc(const struct func_6131b2dc_obj *p)
{
    return (p->flags >> 4) & 1u;
}