struct Data_602a869c {
    unsigned char padding[0x1065];
    unsigned char value;
};

extern "C" int func_602a869c(Data_602a869c *data) {
    return data->value > 0x31u;
}