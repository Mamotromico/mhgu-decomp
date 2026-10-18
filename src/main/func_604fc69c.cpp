struct func_604fc69c_obj {
    unsigned char pad[0xb0];
    unsigned int *values;
};

extern "C" unsigned int func_604fc69c(struct func_604fc69c_obj *obj, unsigned int index)
{
    return obj->values[index];
}