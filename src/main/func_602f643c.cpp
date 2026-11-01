struct func_602f643c_data {
    unsigned char pad[0x321a];
    unsigned short field;
};

extern "C" int func_602f643c(const func_602f643c_data *p) {
    return p->field != 0xffff;
}