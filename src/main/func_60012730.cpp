struct Data_60012730 {
    char pad0[0x3820];
    int count;
    char pad1[4];
    int values[1];
};

extern "C" int func_60012730(Data_60012730* data) {
    int index = data->count;
    if (index != 0) {
        --index;
    }
    return data->values[index];
}