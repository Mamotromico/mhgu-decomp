struct In {
    unsigned int field_0;
    unsigned short field_4;
    unsigned char pad[2];
};

extern "C" unsigned long long func_6130ca4c(struct In *p) {
    return (unsigned long long)p->field_4 | ((unsigned long long)p->field_0 << 32);
}