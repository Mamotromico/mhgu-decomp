struct Data_601694cc {
    unsigned char pad[0x30];
    unsigned int value;
};

extern "C" int func_601694cc(Data_601694cc *data) {
    return (data->value & 0x04000080u) == 0x04000080u;
}