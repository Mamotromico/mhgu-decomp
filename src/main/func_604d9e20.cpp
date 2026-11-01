struct S {
    char pad_0[4];
    unsigned short field_4;
    char pad_6[6];
    unsigned int field_c;
};

extern "C" char* func_604d9e20(void* unused, S* p) {
    char* r = 0;
    if (p == 0)
        return r;
    if (p->field_4 != 0)
        r = (char*)p + p->field_c;
    return r;
}