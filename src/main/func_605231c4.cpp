struct Func605231c4Data {
    char padding[0x2c];
    int value;
};

extern "C" int func_605231c4(const Func605231c4Data* data, int value) {
    int result = 0;
    if (data->value >= value) {
        result = 1;
    }
    return result;
}