struct func_60890adc_obj {
    unsigned char pad[0xf8];
    unsigned int *values;
};

extern "C" unsigned int func_60890adc(struct func_60890adc_obj *obj, unsigned int index)
{
    return obj->values[index];
}