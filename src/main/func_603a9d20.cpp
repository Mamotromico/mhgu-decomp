struct Func603a9d20Data {
    unsigned char padding[0x104];
    unsigned int value;
};

extern "C" int func_603a9d20(Func603a9d20Data* data) {
    return (data->value & 0x60U) == 0x20U;
}