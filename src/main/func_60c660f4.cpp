struct func_60c660f4_s {
    unsigned char pad[0xb4];
    unsigned int field;
};

extern "C" void func_60c660f4(struct func_60c660f4_s *s, unsigned int a, unsigned int b)
{
    s->field = (unsigned int)(unsigned short)a | ((unsigned int)(unsigned short)b << 16);
}