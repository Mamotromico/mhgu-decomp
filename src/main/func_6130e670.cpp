struct func_6130e670_obj {
    unsigned char pad[0x5da];
    unsigned char b0 : 1;
    unsigned char b1 : 1;
    unsigned char b2 : 6;
};

extern "C" int func_6130e670(const struct func_6130e670_obj *p)
{
    return p->b1;
}