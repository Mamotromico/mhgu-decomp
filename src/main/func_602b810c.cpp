struct Func602b810cData {
    char padding[0x31a8];
    int field_31a8;
    int field_31ac;
};

extern "C" void func_602b810c(Func602b810cData *data, int value_31a8, int value_31ac) {
    data->field_31ac = value_31ac;
    data->field_31a8 = value_31a8;
}