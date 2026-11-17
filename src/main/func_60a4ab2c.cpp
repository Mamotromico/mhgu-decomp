extern "C" void func_60a4ab2c(void *self, float v)
{
    char *p = (char *)self;
    float cur = *(float *)(p + 0x80);
    if (cur == v)
        return;
    *(float *)(p + 0x80) = v;
    *(unsigned *)(p + 0x54) |= 0x20000;
}