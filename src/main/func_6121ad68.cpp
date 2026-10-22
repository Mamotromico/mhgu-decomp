struct Data_6121ad68 {
    unsigned char padding[0x10];
    unsigned char value;
};

extern "C" int func_6121ad68(const Data_6121ad68 *data)
{
    return data->value == 0;
}