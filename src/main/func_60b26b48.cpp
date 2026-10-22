struct Data {
    unsigned char pad[0x18];
    unsigned int field_18;
    unsigned int field_1c;
};

extern "C" int func_60b26b48(const Data *data) {
    return data->field_18 == data->field_1c;
}