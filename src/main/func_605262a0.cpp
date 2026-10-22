struct Data {
    char pad[0xd18];
    unsigned int value;
};

extern "C" int func_605262a0(Data* data) {
    return (data->value & 0x3ffffu) != 0;
}