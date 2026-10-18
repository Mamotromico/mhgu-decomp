struct func_60b79e40_s {
    unsigned char pad[0x70];
    unsigned int value;
};

extern "C" unsigned int func_60b79e40(const struct func_60b79e40_s *s, unsigned int i)
{
    return s->value + (i << 7);
}