struct func_6130e8b8_s {
    unsigned char pad[0x5da];
    unsigned char low5 : 5;
    unsigned char flag : 1;
};

extern "C" unsigned int func_6130e8b8(const struct func_6130e8b8_s *p)
{
    return p->flag;
}