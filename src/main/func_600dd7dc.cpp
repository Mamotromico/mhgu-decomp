struct data_600dd7dc {
    unsigned int pad_0;
    unsigned short field_4;
};

extern "C" int func_600dd7dc(const data_600dd7dc* p)
{
    int result = 0;
    if ((p->field_4 & 0x1f) == 0x14)
        result = 1;
    return result;
}