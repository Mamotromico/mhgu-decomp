struct func_60cb1f6c_t {
    unsigned short field_0;
    unsigned short padding_2;
    unsigned int field_4;
};

extern "C" void func_60cb1f6c(func_60cb1f6c_t* p, unsigned int v, unsigned int lo, unsigned int hi)
{
    p->field_0 = (unsigned short)((unsigned char)lo | (hi << 8));
    p->field_4 = v;
}