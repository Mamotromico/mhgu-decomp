struct func_6130e60c_s {
    unsigned char pad[0x5da];
    unsigned char low : 6;
    unsigned char bit : 1;
};

extern "C" unsigned int func_6130e60c(const struct func_6130e60c_s *p)
{
    return p->bit;
}