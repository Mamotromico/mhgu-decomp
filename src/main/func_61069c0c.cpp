struct Data {
    unsigned char pad[0xcbef];
    unsigned char field;
};

extern "C" int func_61069c0c(const Data *data) {
    return data->field == 3;
}