struct arg_60436588 {
    unsigned char padding[4];
    unsigned char field;
};

extern "C" int func_60436588(const arg_60436588* arg) {
    int result = 0;
    if (arg->field == 5) {
        result = 1;
    }
    return result;
}