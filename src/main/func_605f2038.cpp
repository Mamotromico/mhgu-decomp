struct Data_605f2038 {
    unsigned char pad_0x00[0x50];
    unsigned int field_0x50;
    unsigned char pad_0x54[0x4];
    unsigned int field_0x58;
};

extern "C" void func_605f2038(Data_605f2038 *obj, unsigned int value)
{
    obj->field_0x58 = value;
    obj->field_0x50 |= 3u;
}