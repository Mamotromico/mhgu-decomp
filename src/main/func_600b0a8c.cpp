struct FuncData {
    unsigned char padding[0x4f4];
    float value;
};

extern "C" int func_600b0a8c(FuncData* data) {
    return data->value > 0.0f;
}