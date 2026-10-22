struct func_6121aa6c_struct {
    unsigned char padding[0xc];
    unsigned char field;
};

extern "C" int func_6121aa6c(func_6121aa6c_struct* obj)
{
    if (obj->field == 0) {
        return 1;
    }
    return 0;
}