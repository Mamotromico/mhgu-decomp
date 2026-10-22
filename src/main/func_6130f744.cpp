struct func_6130f744_arg {
    unsigned char pad[0x23];
    unsigned char field;
};

extern "C" int func_6130f744(func_6130f744_arg *arg) {
    int result = 0;
    if (arg->field == 2) {
        result = 1;
    }
    return result;
}