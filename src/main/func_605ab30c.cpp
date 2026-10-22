struct func_605ab30c_struct
{
    unsigned char pad[0x50];
    unsigned int field_0x50;
};

extern "C" int func_605ab30c(func_605ab30c_struct *obj)
{
    int result = 0;
    if (obj->field_0x50 > 1u)
        result = 1;
    return result;
}