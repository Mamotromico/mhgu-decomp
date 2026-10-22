struct Data_606d3558 {
    unsigned char pad[0x16c0];
    unsigned short value;
};

extern "C" int func_606d3558(Data_606d3558 *data) {
    int result = 0;
    if (data->value != 0xb) {
        result = 1;
    }
    return result;
}