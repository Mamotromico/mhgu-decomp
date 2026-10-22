struct Data_602840fc {
    unsigned char pad[0x1380];
    unsigned int value;
};

extern "C" int func_602840fc(const Data_602840fc *data) {
    int result = 0;
    if (data->value == 0x68)
        result = 1;
    return result;
}