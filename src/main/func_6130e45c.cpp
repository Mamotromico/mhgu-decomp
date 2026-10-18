struct func_6130e45c_obj {
    unsigned char pad[0x5d8];
    unsigned int field;
};

extern "C" int func_6130e45c(const struct func_6130e45c_obj *obj)
{
    return obj->field & 1;
}