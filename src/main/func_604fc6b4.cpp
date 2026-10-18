struct func_604fc6b4_obj {
    unsigned char pad[0xd8];
    unsigned int *field;
};

extern "C" unsigned int func_604fc6b4(const struct func_604fc6b4_obj *obj, unsigned int idx)
{
    return obj->field[idx];
}