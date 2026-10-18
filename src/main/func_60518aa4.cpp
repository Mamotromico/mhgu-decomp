struct func_60518aa4_obj {
    unsigned char pad[0x58];
    volatile unsigned int field_58;
    volatile unsigned char field_5c;
};

extern "C" void func_60518aa4(struct func_60518aa4_obj *obj,
                              unsigned int value,
                              unsigned char flag)
{
    obj->field_58 = value;
    obj->field_5c = flag;
}