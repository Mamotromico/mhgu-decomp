struct Data {
    unsigned char pad[0x1068];
    unsigned char value;
};

extern "C" int func_602a80e8(const Data* data) {
    return (data->value >> 5) & 1;
}