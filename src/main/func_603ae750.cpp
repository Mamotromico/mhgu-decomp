struct func_603ae750_obj {
    unsigned char pad[0xb8];
    unsigned char flags;
};

extern "C" unsigned int func_603ae750(const struct func_603ae750_obj *obj)
{
    return (obj->flags >> 2) & 1;
}