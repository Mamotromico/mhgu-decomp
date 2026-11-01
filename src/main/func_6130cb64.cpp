struct Data {
    int field_0;
    unsigned short field_4;
};

extern "C" int func_6130cb64(Data* p) {
    if (p->field_0 == 0)
        return 0;
    return p->field_4 != 0 ? 1 : 0;
}