struct func_603ae75c_obj {
    unsigned char pad[0xb9];
    unsigned char flags;
};

extern "C" unsigned int func_603ae75c(const struct func_603ae75c_obj *p)
{
    return (p->flags >> 4) & 1u;
}