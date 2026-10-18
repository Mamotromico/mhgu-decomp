struct func_60871d58_obj {
    unsigned char pad[0x488];
    unsigned char field;
};

extern "C" unsigned int func_60871d58(const struct func_60871d58_obj *p)
{
    return (p->field >> 3) & 1;
}