struct Data_602f1900 {
    unsigned char pad[0x2898];
    unsigned int value;
};

extern "C" int func_602f1900(Data_602f1900 *p) {
    int result = 0;
    if (p->value > 0x31u) {
        result = 1;
    }
    return result;
}