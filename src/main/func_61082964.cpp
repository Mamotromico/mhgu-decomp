struct Func61082964Data {
    unsigned char pad[0xcb30];
    unsigned char field;
};

extern "C" int func_61082964(Func61082964Data *data)
{
    unsigned char value = data->field;
    int result = 0;
    if (value != 0xff) {
        result = 1;
    }
    return result;
}