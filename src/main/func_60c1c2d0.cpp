extern "C" unsigned func_60c717fc(unsigned a, unsigned b);

extern "C" unsigned func_60c1c2d0(void *p)
{
    unsigned a = *(unsigned *)((char *)p + 0x18);
    unsigned b = *(unsigned *)((char *)p + 0x44);
    return func_60c717fc(a, b);
}