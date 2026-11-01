extern "C" int func_600bad1c(char *base)
{
    unsigned int v = *(unsigned int *)(base + 0x1428);
    float f = *(float *)((char *)v + 0x5db4);
    return f > 0.0f ? 1 : 0;
}