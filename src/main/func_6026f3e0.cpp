struct Data {
    unsigned char pad[0x506];
    unsigned short field;
};

extern "C" int func_6026f3e0(const Data *data, unsigned int bit) {
    return (data->field & (1u << bit)) != 0;
}