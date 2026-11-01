struct Func600dcdbc_Data {
    unsigned char pad0[0x4];
    unsigned short value;
    unsigned char pad1[0x1d - 0x6];
    unsigned char result;
};

extern "C" int func_600dcdbc(const Func600dcdbc_Data *data) {
    if ((data->value & 0x1fU) == 0x14U) {
        return data->result;
    }
    return 0;
}