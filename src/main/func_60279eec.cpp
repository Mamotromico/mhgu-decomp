extern "C" int func_6027a014(void *p);

extern "C" void func_60279eec(char *self, unsigned char val)
{
    *(unsigned char *)(self + 0x68) = val;
    char *r = (char *)func_6027a014(self);
    if (r)
        *(unsigned char *)(r + 0x2738) = val;
}