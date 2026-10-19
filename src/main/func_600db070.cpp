struct Data_600db070 {
    unsigned char pad[8];
    unsigned short field;
};

extern "C" int func_600db070(const Data_600db070 *data)
{
    return data->field != 0;
}