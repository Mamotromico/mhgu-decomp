struct Data {
    unsigned char pad[0x344];
    unsigned int value_344;
    unsigned int value_348;
};

extern "C" void func_605045e8(Data *data) {
    data->value_348 = 0x46c4e000u;
    data->value_344 = 1;
}