struct func_600e79b4_data {
    unsigned char pad[0x23c];
    unsigned short values[3];
};

extern "C" void func_600e79b4(func_600e79b4_data *data, unsigned int index, unsigned short value) {
    if (index <= 2u) {
        data->values[index] = value;
    }
}